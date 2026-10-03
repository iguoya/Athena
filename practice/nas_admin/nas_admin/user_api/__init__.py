"""全局学习者目录的 REST API，挂在 nas_admin 后台里（ADR 0074、0075）。

学习者是「这个人」，不属于驾考或任何一个应用，所以这套接口不挂 `/api/driver` 前缀；
应用里不认证（主仓库 ADR 0077）。接口说明见 `docs/user-api.md`。
"""

from __future__ import annotations

from flask import Flask
from sqlalchemy import Engine

from nas_admin.user_api import directory
from nas_admin.user_api.routes import bp


def init_user_api(app: Flask, *, engine: Engine | None = None) -> None:
    """注册蓝图。`engine` 只给测试注入用；生产用后台库（见 directory.engine）。"""
    if engine is not None:
        app.extensions[directory.ENGINE_KEY] = engine
    app.register_blueprint(bp)
    csrf = app.extensions.get("csrf")
    if csrf is not None:
        csrf.exempt(bp)
