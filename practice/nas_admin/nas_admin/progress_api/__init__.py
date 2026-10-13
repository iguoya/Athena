"""学习进度的通用同步接口，挂在 nas_admin 后台里（主仓库 ADR 0155）。

各学习应用的本地 SQLite 进度库由启动器里的同步代理推拉到这里；服务端不认识任何
应用的表结构，只按 (学习者, 应用, 表名, 主键) 存 JSON 行。应用里不认证（ADR 0077）。
接口说明见 `docs/progress-api.md`。
"""

from __future__ import annotations

from flask import Flask
from sqlalchemy import Engine

from nas_admin.progress_api import store
from nas_admin.progress_api.routes import bp


def init_progress_api(app: Flask, *, engine: Engine | None = None) -> None:
    """注册蓝图。`engine` 只给测试注入用；生产用后台库（见 store.engine）。"""
    if engine is not None:
        app.extensions[store.ENGINE_KEY] = engine
    app.register_blueprint(bp)
    csrf = app.extensions.get("csrf")
    if csrf is not None:
        csrf.exempt(bp)
