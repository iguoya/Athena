"""请求来源与限流（主仓库 ADR 0077）。

应用里**不认证**：内网直连可信，外网由 Cloudflare Access 在边缘把守整个主机名。这里只做
一件事——不让失控的客户端把库打爆，所以按来源地址限流。

来源地址优先取 `Cf-Connecting-Ip`（经 Cloudflare 隧道进来的请求，连接地址是隧道本身，
没有区分度）；没有这个头就是内网直连，取连接地址。头可以被内网里的人随便写，影响的只是
限流用的键，没有安全后果。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from flask import request

RATE_LIMIT = 300  # 每个来源地址每分钟最多请求数


def client_address() -> str:
    forwarded = request.headers.get("Cf-Connecting-Ip", "").strip()
    return forwarded[:64] or request.remote_addr or "unknown"


_hits: dict[str, deque[float]] = defaultdict(deque)
_hits_lock = threading.Lock()


def allow(key: str, *, limit: int | None = None, window: float = 60.0) -> bool:
    """滑动窗口限流（进程内）。路由上就一个进程，够用；多进程部署时再换共享存储。"""
    limit = RATE_LIMIT if limit is None else limit
    now = time.monotonic()
    with _hits_lock:
        q = _hits[key]
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
