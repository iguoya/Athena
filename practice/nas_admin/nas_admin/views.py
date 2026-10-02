"""首页仪表盘与健康检查。"""

from __future__ import annotations

import platform
import sys
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError
from urllib.parse import urlsplit

from flask import current_app, jsonify
from flask_appbuilder import expose
from flask_appbuilder.views import IndexView
from sqlalchemy import text


def _dist_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "未知"


def _database_label() -> str:
    """连接串里的主机与库名，够 health/首页用了，不泄密码。"""
    parsed = urlsplit(current_app.config["SQLALCHEMY_DATABASE_URI"])
    return f"{parsed.hostname}:{parsed.port or 5432}{parsed.path}"


def _database_server() -> str:
    """查一次 PG 的版本串——打开首页就能看出数据库通不通。"""
    from nas_admin import db

    try:
        row = db.session.execute(text("SELECT version()")).scalar_one()
        return row.split(" on ")[0]
    except Exception as error:  # 数据库不在线时首页不该白屏
        return f"不可达：{type(error).__name__}"


def health():
    """探活端点：app.json 的 http ready 与部署脚本都打它。"""
    return jsonify(
        ok=True,
        app="athena-nas-admin",
        python=sys.version.split()[0],
        database=_database_label(),
    )


class DashboardIndexView(IndexView):
    """后台首页：FAB 框架的导航在外，内容区换成自己的状态卡片。

    指标全部来自跨平台标准库（platform/sys/importlib）加一次数据库
    查询，本机 Windows 开发与路由器 Linux 运行显示同一套东西；系统级
    监控（CPU/内存）是后续功能，先不引平台分支。
    """

    @expose("/")
    def index(self):
        cards = [
            ("运行环境", platform.platform()),
            ("Python", sys.version.split()[0]),
            ("Flask-AppBuilder", _dist_version("Flask-AppBuilder")),
            ("数据库", _database_label()),
            ("数据库服务", _database_server()),
            ("服务器时间", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ]
        # 必须用 self.render_template：只有它注入 base_template 等 FAB 上下文。
        return self.render_template("dashboard.html", cards=cards)
