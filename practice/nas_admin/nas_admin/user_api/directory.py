"""全局学习者目录（ADR 0073、0074、0075）：谁是学习者、叫什么、编号几号。

放在后台库（nas_admin）里，与设备令牌同库：这是仓库级设施，不属于任何一个应用的个人
数据库。学习者编号是服务端顺序分配的纯数字（1～999），永不变、不复用、不提供删除；
名字不要求唯一，重名由编号区分。

名字比较忽略大小写和首尾空白：`name_key` 存折叠后的名字，查询只比这一列，不依赖
数据库方言的 `lower()`（SQLite 只折 ASCII，PG 按区域设置）。
"""

from __future__ import annotations

import threading
import weakref
import zlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, Connection, Engine, Index, Integer, MetaData, Table, Text, func, insert, select, text, update

MAX_ID = 999  # 家用够了；超出就拒绝登记，不悄悄回绕
MAX_NAME = 64

_metadata = MetaData()
users = Table(
    "athena_users",
    _metadata,
    # 编号由本模块在锁内分配，不用数据库自增（SQLite/PG 行为不一，也不想有空洞之外的惊喜）。
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("name", Text, nullable=False),
    Column("name_key", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
    Index("athena_users_name_key", "name_key"),
)

_ready_lock = threading.Lock()
_ready_for: "weakref.WeakSet[Engine]" = weakref.WeakSet()


class DirectoryFull(RuntimeError):
    """编号用完（超过 MAX_ID）。"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def name_key(name: str) -> str:
    """名字的比较键：去首尾空白、折叠大小写。"""
    return name.strip().casefold()


def ensure_table(engine: Engine) -> None:
    with _ready_lock:
        if engine not in _ready_for:
            users.create(bind=engine, checkfirst=True)
            _ready_for.add(engine)


def _lock(conn: Connection) -> None:
    """登记串行化：「取最大编号再加一」在并发下不会分出同一个号（只在 PG 上生效）。"""
    if conn.dialect.name == "postgresql":
        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": zlib.crc32(b"user_api:athena_users")})


def _public(row: Any) -> dict[str, Any]:
    return {"id": int(row["id"]), "name": row["name"]}


def register(conn: Connection, name: str) -> dict[str, Any]:
    """新建学习者，返回 `{id, name}`。重名照样新建（身份是编号，ADR 0075 决策 4）。"""
    clean = name.strip()
    _lock(conn)
    top = conn.execute(select(func.coalesce(func.max(users.c.id), 0))).scalar_one()
    new_id = int(top) + 1
    if new_id > MAX_ID:
        raise DirectoryFull(f"学习者编号已用到 {MAX_ID}")
    now = _now()
    conn.execute(
        insert(users).values(id=new_id, name=clean, name_key=name_key(clean), created_at=now, updated_at=now)
    )
    return {"id": new_id, "name": clean}


def find(conn: Connection, name: str, user_id: int | None = None) -> list[dict[str, Any]]:
    """按名字（可再按编号）找学习者；返回全部匹配，按编号升序。"""
    stmt = select(users).where(users.c.name_key == name_key(name))
    if user_id is not None:
        stmt = stmt.where(users.c.id == user_id)
    return [_public(row) for row in conn.execute(stmt.order_by(users.c.id)).mappings()]


def get(conn: Connection, user_id: int) -> dict[str, Any] | None:
    row = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
    return _public(row) if row else None


def rename(conn: Connection, user_id: int, name: str) -> dict[str, Any] | None:
    """改显示名；编号不变，不触碰任何个人数据。没有这个编号返回 None。"""
    clean = name.strip()
    changed = conn.execute(
        update(users)
        .where(users.c.id == user_id)
        .values(name=clean, name_key=name_key(clean), updated_at=_now())
    ).rowcount
    return {"id": user_id, "name": clean} if changed else None
