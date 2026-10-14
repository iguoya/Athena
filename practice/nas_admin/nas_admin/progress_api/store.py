"""进度行的存储与合并（ADR 0155 决策 4、5）。

一行 = 某学习者在某应用某张表里的某条记录，内容是客户端原样传来的 JSON 对象。
合并规则由客户端按表声明、随每行带来：

- `append`：事件，同一业务键只记第一次，之后重复上传一律忽略（取并集）。删除用**墓碑**表达
  （ADR 0156）：带 `deleted` 的一行把存活的事件标成已删，原数据留着不清；墓碑只增不减，
  已删的事件不会再被任何写入复活，重复的墓碑也一律忽略；
- `lww`：可变记录，按 (更新时间, 设备) 新者胜，删除是带 `deleted` 标记的一行，不真删。

`seq` 是全局单调序号，每次写入（新增或改写）都取新号，客户端用它做增量拉取的游标。
"""

from __future__ import annotations

import threading
import weakref
import zlib
from datetime import datetime, timezone
from typing import Any

from flask import current_app
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Connection,
    Engine,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    func,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB

ENGINE_KEY = "progress_api.engine"  # app.extensions 里放注入的 Engine（测试用）
MODES = ("append", "lww")

_metadata = MetaData()
rows = Table(
    "athena_progress_rows",
    _metadata,
    Column("learner", Integer, primary_key=True, autoincrement=False),
    Column("app", Text, primary_key=True),
    Column("tbl", Text, primary_key=True),
    Column("pk", Text, primary_key=True),
    Column("data", JSON().with_variant(JSONB(), "postgresql"), nullable=True),
    Column("mode", Text, nullable=False),
    Column("stamp", Text, nullable=False),
    Column("deleted", Boolean, nullable=False, default=False),
    Column("device", Text, nullable=False),
    # 序号由本模块在锁内分配，不用数据库自增。
    Column("seq", BigInteger, nullable=False),
    Column("received_at", Text, nullable=False),
    Index("athena_progress_rows_pull", "learner", "app", "seq"),
    # 每次推送都要取全表的最大序号分配新号；没有单独的 seq 索引它就是全表扫描，行数涨上去会越推越慢。
    Index("athena_progress_rows_seq", "seq"),
)

_ready_lock = threading.Lock()
_ready_for: "weakref.WeakSet[Engine]" = weakref.WeakSet()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def engine() -> Engine:
    """进度行所在的库：后台库（nas_admin）。测试注入内存库。"""
    injected = current_app.extensions.get(ENGINE_KEY)
    if injected is not None:
        return injected
    from nas_admin import db  # 延迟导入，避免循环依赖

    return db.engine


def ensure_table(engine: Engine) -> None:
    with _ready_lock:
        if engine not in _ready_for:
            rows.create(bind=engine, checkfirst=True)
            # create(checkfirst) 见表已存在就整个跳过，已部署的旧表要单独补上后加的索引。
            for index in rows.indexes:
                index.create(bind=engine, checkfirst=True)
            _ready_for.add(engine)


def _lock(conn: Connection) -> None:
    """写入串行化：「取最大序号再加一」在并发下不会分出同一个号（只在 PG 上生效）。"""
    if conn.dialect.name == "postgresql":
        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": zlib.crc32(b"progress_api:rows")})


def push(conn: Connection, learner: int, app: str, device: str, incoming: list[dict[str, Any]]) -> dict[str, int]:
    """合并一批行，返回 `{accepted, ignored, cursor}`；cursor 是当前最大序号。"""
    _lock(conn)
    top = int(conn.execute(select(func.coalesce(func.max(rows.c.seq), 0))).scalar_one())
    now = _now()
    accepted = ignored = 0
    for item in incoming:
        key = (
            (rows.c.learner == learner)
            & (rows.c.app == app)
            & (rows.c.tbl == item["tbl"])
            & (rows.c.pk == item["pk"])
        )
        current = conn.execute(select(rows.c.stamp, rows.c.device, rows.c.deleted).where(key)).mappings().first()
        values = dict(
            data=None if item["deleted"] else item["data"],
            mode=item["mode"],
            stamp=item["stamp"],
            deleted=item["deleted"],
            device=device,
            received_at=now,
        )
        if current is None:
            top += 1
            conn.execute(
                insert(rows).values(learner=learner, app=app, tbl=item["tbl"], pk=item["pk"], seq=top, **values)
            )
            accepted += 1
            continue
        if item["mode"] == "append":
            # 事件只记第一次；唯一能改它的是墓碑——存活 → 已删，单向、幂等，原数据不动。
            if not (item["deleted"] and not current["deleted"]):
                ignored += 1
                continue
            top += 1
            conn.execute(
                update(rows)
                .where(key)
                .values(deleted=True, stamp=item["stamp"], device=device, received_at=now, seq=top)
            )
            accepted += 1
            continue
        # 可变记录比 (更新时间, 设备)，同一时刻也有确定的胜者。
        if (item["stamp"], device) <= (current["stamp"], current["device"]):
            ignored += 1
            continue
        top += 1
        conn.execute(update(rows).where(key).values(seq=top, **values))
        accepted += 1
    return {"accepted": accepted, "ignored": ignored, "cursor": top}


def pull(conn: Connection, learner: int, app: str, since: int, limit: int) -> dict[str, Any]:
    """序号大于 `since` 的行，按序号升序；`more` 表示后面还有，客户端拿 `next` 接着拉。"""
    found = list(
        conn.execute(
            select(rows)
            .where(rows.c.learner == learner, rows.c.app == app, rows.c.seq > since)
            .order_by(rows.c.seq)
            .limit(limit + 1)
        ).mappings()
    )
    more = len(found) > limit
    found = found[:limit]
    return {
        "rows": [
            {
                "tbl": r["tbl"],
                "pk": r["pk"],
                "data": r["data"],
                "mode": r["mode"],
                "stamp": r["stamp"],
                "deleted": bool(r["deleted"]),
                "device": r["device"],
                "seq": int(r["seq"]),
            }
            for r in found
        ],
        "next": int(found[-1]["seq"]) if found else since,
        "more": more,
    }
