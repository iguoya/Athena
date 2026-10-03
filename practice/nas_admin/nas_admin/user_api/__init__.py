"""全局学习者目录的 REST API，挂在 nas_admin 后台里（ADR 0074、0075）。

学习者是「这个人」，不属于驾考或任何一个应用，所以这套接口不挂 `/api/driver` 前缀；
认证复用驾考 API 的设备令牌（令牌表本来就在后台库里）。接口说明见 `docs/user-api.md`。
"""

from __future__ import annotations

from flask import Flask
from sqlalchemy import Engine

from nas_admin.driver_api import auth
from nas_admin.user_api.routes import bp


def init_user_api(app: Flask, *, token_engine: Engine | None = None) -> None:
    """注册蓝图。`token_engine` 只给测试注入用；生产走后台库（见 driver_api/auth.py）。"""
    if token_engine is not None:
        app.extensions[auth.TOKEN_ENGINE_KEY] = token_engine
    app.register_blueprint(bp)
    csrf = app.extensions.get("csrf")
    if csrf is not None:
        csrf.exempt(bp)
