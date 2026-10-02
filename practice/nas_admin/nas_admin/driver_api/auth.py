"""设备令牌认证。

每台设备一个随机令牌，**服务端只存 SHA-256 哈希**，库被读走也还原不出令牌；丢了一台
设备就撤销那一个，不影响别的。令牌放 `Authorization: Bearer <token>` 请求头。

令牌表放在后台自己的库（nas_admin）里，不放进 driver 的个人数据库：driver 库只装
学习记录，认证信息归后台管。

这一层不依赖「前面有 Cloudflare Access」：Access 挡的是陌生人，设备令牌挡的是
「已经进来了但不该写数据」的人，也让每条写入能追溯到设备。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
import weakref
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import current_app
from sqlalchemy import (
    Column,
    Engine,
    Integer,
    MetaData,
    Table,
    Text,
    insert,
    select,
    update,
)

TOKEN_ENGINE_KEY = "driver_api.token_engine"  # 测试注入用
TOKEN_PREFIX = "dapi_"

_metadata = MetaData()
tokens = Table(
    "driver_api_tokens",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text, nullable=False),
    Column("token_hash", Text, nullable=False, unique=True),
    Column("created_at", Text, nullable=False),
    Column("last_used_at", Text),
    Column("revoked_at", Text),
)

_ready_lock = threading.Lock()
# 已建过表的 Engine；弱引用，Engine 回收后自动出集合，避免对象地址复用造成误判。
_ready_for: "weakref.WeakSet[Engine]" = weakref.WeakSet()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_engine() -> Engine:
    injected = current_app.extensions.get(TOKEN_ENGINE_KEY)
    if injected is not None:
        return injected
    from nas_admin import db  # 延迟导入，避免循环依赖

    return db.engine


def ensure_table(engine: Engine) -> None:
    with _ready_lock:
        if engine not in _ready_for:
            tokens.create(bind=engine, checkfirst=True)
            _ready_for.add(engine)


# ---------------------------------------------------------------- 令牌管理（CLI 与测试用）


def create_token(engine: Engine, name: str) -> tuple[int, str]:
    """生成并保存一个新令牌；明文只在这里返回一次，库里只有哈希。"""
    ensure_table(engine)
    token = TOKEN_PREFIX + secrets.token_urlsafe(32)
    with engine.begin() as conn:
        result = conn.execute(insert(tokens).values(name=name, token_hash=hash_token(token), created_at=_now()))
        return int(result.inserted_primary_key[0]), token


def revoke_token(engine: Engine, token_id: int) -> bool:
    ensure_table(engine)
    with engine.begin() as conn:
        return bool(
            conn.execute(
                update(tokens).where((tokens.c.id == token_id) & tokens.c.revoked_at.is_(None)).values(revoked_at=_now())
            ).rowcount
        )


def list_tokens(engine: Engine) -> list[dict[str, Any]]:
    ensure_table(engine)
    with engine.connect() as conn:
        return [
            {k: v for k, v in row.items() if k != "token_hash"}
            for row in conn.execute(select(tokens).order_by(tokens.c.id)).mappings()
        ]


# ---------------------------------------------------------------- 请求认证


def authenticate(header: str | None) -> dict[str, Any] | None:
    """校验 Authorization 头，返回设备信息；无效、已撤销、格式不对都返回 None。"""
    if not header or not header.startswith("Bearer "):
        return None
    token = header[len("Bearer ") :].strip()
    if not token.startswith(TOKEN_PREFIX) or len(token) > 200:
        return None
    digest = hash_token(token)
    engine = token_engine()
    ensure_table(engine)
    with engine.begin() as conn:
        row = conn.execute(select(tokens).where(tokens.c.token_hash == digest)).mappings().first()
        # 哈希已按唯一索引精确匹配；compare_digest 只是不留下时序差异。
        if row is None or not hmac.compare_digest(row["token_hash"], digest) or row["revoked_at"]:
            return None
        # 最近使用时间最多一分钟写一次，免得每个请求都写库。
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not row["last_used_at"] or row["last_used_at"] < cutoff:
            conn.execute(update(tokens).where(tokens.c.id == row["id"]).values(last_used_at=_now()))
        return {"id": int(row["id"]), "name": row["name"]}


# ---------------------------------------------------------------- 速率限制

RATE_LIMIT = 300  # 每个令牌每分钟最多请求数
_hits: dict[int, deque[float]] = defaultdict(deque)
_hits_lock = threading.Lock()


def allow(device_id: int, *, limit: int = RATE_LIMIT, window: float = 60.0) -> bool:
    """滑动窗口限流（进程内）。路由上就一个进程，够用；多进程部署时再换共享存储。"""
    now = time.monotonic()
    with _hits_lock:
        q = _hits[device_id]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


def reset_rate_limits() -> None:
    """测试用：清空计数。"""
    with _hits_lock:
        _hits.clear()
