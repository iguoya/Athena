"""驾考（driver）进度数据的 REST API，挂在 nas_admin 后台里。

为什么有它：驾考客户端在内网直连路由器上的 PostgreSQL，离开内网就连不上；数据库端口
又不该暴露到公网。这里把「读写进度」做成一层窄接口，客户端只拿一个可撤销的设备令牌，
数据库密码只留在路由器上。接口说明见 `docs/driver-api.md`。
"""

from __future__ import annotations

from flask import Flask
from sqlalchemy import Engine

from nas_admin.driver_api import auth, store
from nas_admin.driver_api.routes import bp


def init_driver_api(app: Flask, *, driver_engine: Engine | None = None, token_engine: Engine | None = None) -> None:
    """注册蓝图。两个 Engine 参数只给测试注入用；生产走配置（见 store.py / auth.py）。"""
    if driver_engine is not None:
        app.extensions[store.ENGINE_KEY] = driver_engine
    if token_engine is not None:
        app.extensions[auth.TOKEN_ENGINE_KEY] = token_engine
    app.register_blueprint(bp)
    # 若应用启用了全局 CSRF（flask-wtf），API 靠令牌认证、没有浏览器会话，需要豁免。
    csrf = app.extensions.get("csrf")
    if csrf is not None:
        csrf.exempt(bp)
