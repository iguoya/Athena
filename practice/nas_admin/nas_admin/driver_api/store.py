"""driver 进度库的读写。全部用 SQLAlchemy Core 构造，参数一律绑定，不拼 SQL。

连接用专用低权限角色（只有表的增删改查，没有 DDL）。表不存在、库不可达都不在这里
吞掉，由路由层映射成 503，避免把数据库细节返回给调用者。
"""

from __future__ import annotations

import json
import os
import threading
import zlib
from pathlib import Path
from typing import Any, Iterable

from flask import current_app
from sqlalchemy import (
    Connection,
    Engine,
    and_,
    cast,
    create_engine,
    delete,
    exists,
    func,
    insert,
    literal,
    select,
    text,
    update,
)

from nas_admin.driver_api import schema
from nas_admin.driver_api.resources import APPEND_ONLY, Resource

ENGINE_KEY = "driver_api.engine"  # app.extensions 里放注入的 Engine（测试用）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

_engine_lock = threading.Lock()
_engine: Engine | None = None


# 可缺省字段的默认值：数值计数列归 0，场合标记归平时练习（driver ADR 0057）。
_COLUMN_DEFAULTS = {"duration_ms": 0, "hesitant": 0, "read": 0, "kind": "practice"}


class NotConfigured(RuntimeError):
    """没配 driver 数据库连接串。"""


def _database_url() -> str:
    """环境变量 `DRIVER_API_DATABASE_URL` 或 `driver-db.json`（已 gitignore，`{"url": ...}`）。"""
    from_env = os.environ.get("DRIVER_API_DATABASE_URL")
    if from_env:
        return from_env
    local = BASE_DIR / "driver-db.json"
    if local.is_file():
        try:
            return str(json.loads(local.read_text(encoding="utf-8"))["url"])
        except (json.JSONDecodeError, KeyError):
            raise NotConfigured("driver-db.json 格式不对") from None
    raise NotConfigured("未配置 driver 数据库连接串")


def _normalize(url: str) -> str:
    # 连接串常写成 postgresql://；SQLAlchemy 默认会去找 psycopg2，这里装的是 psycopg 3。
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def engine() -> Engine:
    injected = current_app.extensions.get(ENGINE_KEY)
    if injected is not None:
        return injected
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = create_engine(
                _normalize(_database_url()),
                pool_size=3,
                max_overflow=2,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5},
            )
        return _engine


def _lock(conn: Connection, name: str) -> None:
    """同一张表的写入串行化：「先查再插」在并发下不会插出重复行。

    只在 PG 上生效（事务级咨询锁，事务结束自动释放）；测试用的 SQLite 本身单写者。
    """
    if conn.dialect.name == "postgresql":
        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": zlib.crc32(f"driver_api:{name}".encode())})


# ---------------------------------------------------------------- 追加型资源


def insert_missing(conn: Connection, res: Resource, items: Iterable[dict[str, Any]], user: str) -> tuple[int, int]:
    """逐条「不存在才插入」，返回 (新增条数, 已存在而跳过的条数)。

    `user` 来自请求头而不是 item：客户端的记录里没有这个字段，同一批数据在两个
    用户名下是两份独立的历史（ADR 0071）。
    """
    table = res.table
    columns = [c for c in table.columns if c.name != "id"]
    inserted = skipped = 0
    _lock(conn, table.name)
    for item in items:
        row = {c.name: item.get(c.name, _COLUMN_DEFAULTS.get(c.name)) for c in columns}
        row["user"] = user
        # SELECT 列表里的绑定参数必须带类型，否则 PG 报「无法确定参数类型」。
        values = [cast(literal(row[c.name]), c.type) for c in columns]
        duplicate = exists(select(literal(1)).select_from(table).where(and_(*[table.c[k] == row[k] for k in res.dedupe])))
        # 不能靠 rowcount：PG 驱动对 INSERT…SELECT 的 rowcount 不可靠（可能是 -1，
        # 而 -1 是真值，会把「跳过」误报成「插入」）。RETURNING 有行才是真的插入了。
        stmt = insert(table).from_select([c.name for c in columns], select(*values).where(~duplicate)).returning(table.c.id)
        if conn.execute(stmt).first() is not None:
            inserted += 1
        else:
            skipped += 1
    return inserted, skipped


def list_after(conn: Connection, res: Resource, user: str, after_id: int, limit: int) -> tuple[list[dict[str, Any]], bool]:
    """按 id 升序取该用户 after_id 之后的记录；多取一位判断后面还有没有。

    id 是全表序列（不分用户），同一用户的 id 不连续，但「大于游标取下一段」的
    语义照常成立——游标只在该用户的行流上前进。
    """
    table = res.table
    rows = (
        conn.execute(
            select(table).where(table.c.id > after_id, table.c.user == user).order_by(table.c.id).limit(limit + 1)
        )
        .mappings()
        .all()
    )
    has_more = len(rows) > limit
    # user 是请求方自己的身份，不随每行回传（字段契约与客户端本地表一致，ADR 0071）。
    return [{k: v for k, v in dict(r).items() if k != "user"} for r in rows[:limit]], has_more


def mark_notices_read(conn: Connection, user: str) -> int:
    n = schema.notices
    return conn.execute(update(n).where(n.c.user == user, n.c.read == 0).values(read=1)).rowcount


# ---------------------------------------------------------------- 成就


def list_achievements(conn: Connection, user: str) -> list[dict[str, Any]]:
    a = schema.achievements
    rows = conn.execute(select(a.c.key, a.c.at).where(a.c.user == user).order_by(a.c.at, a.c.key)).mappings()
    return [dict(r) for r in rows]


def put_achievement(conn: Connection, user: str, key: str, at: str) -> str:
    """成就按 (用户, 键) 幂等；已存在时保留**更早**的解锁时间（两台机器各自解锁，以先到者为准）。"""
    a = schema.achievements
    _lock(conn, a.name)
    current = conn.execute(select(a.c.at).where(a.c.user == user, a.c.key == key)).scalar_one_or_none()
    if current is None:
        conn.execute(insert(a).values(user=user, key=key, at=at))
        return at
    if at < current:
        conn.execute(update(a).where(a.c.user == user, a.c.key == key).values(at=at))
        return at
    return current


# ---------------------------------------------------------------- 试卷草稿


def get_draft(conn: Connection, user: str, key: str) -> dict[str, Any] | None:
    d = schema.exam_drafts
    row = conn.execute(select(d).where(d.c.user == user, d.c.draft_key == key)).mappings().first()
    return {k: v for k, v in dict(row).items() if k != "user"} if row else None


def put_draft(conn: Connection, user: str, key: str, fields: dict[str, Any]) -> bool:
    """整份覆盖；若库里的 saved_at 比传来的更新，则不覆盖（返回 False）。"""
    d = schema.exam_drafts
    _lock(conn, d.name)
    values = {**fields, "saved_at": fields.get("saved_at")}
    current = conn.execute(select(d.c.saved_at).where(d.c.user == user, d.c.draft_key == key)).first()
    if current is None:
        conn.execute(insert(d).values(user=user, draft_key=key, **values))
        return True
    stored, incoming = current[0], values["saved_at"]
    if stored and incoming and incoming < stored:
        return False
    conn.execute(update(d).where(d.c.user == user, d.c.draft_key == key).values(**values))
    return True


def delete_draft(conn: Connection, user: str, key: str) -> None:
    d = schema.exam_drafts
    conn.execute(delete(d).where(d.c.user == user, d.c.draft_key == key))


# ---------------------------------------------------------------- 统计


def stats(conn: Connection, user: str) -> dict[str, dict[str, int]]:
    """该用户各表条数与最大 id：客户端用来快速判断「我这边有没有落后」，不必拉全量。"""
    out: dict[str, dict[str, int]] = {}
    for name, res in APPEND_ONLY.items():
        t = res.table
        count, max_id = conn.execute(
            select(func.count(), func.coalesce(func.max(t.c.id), 0)).where(t.c.user == user)
        ).one()
        out[name] = {"count": int(count), "max_id": int(max_id)}
    a = schema.achievements
    out["achievements"] = {
        "count": int(conn.execute(select(func.count()).select_from(a).where(a.c.user == user)).scalar_one()),
        "max_id": 0,
    }
    return out
