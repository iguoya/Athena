"""AthenaNAS 后台管理（Flask-AppBuilder 5）。

从路由器上原来的单文件 Flask 演化而来（原 /opt/webapp/app.py 只有两个
端点）：/api/health 原样保留——它同时是 app.json 的 http 探活目标。
"""

from __future__ import annotations

from flask import Flask

from flask_appbuilder import AppBuilder
from flask_appbuilder.models.sqla.base import SQLA

from nas_admin.views import DashboardIndexView, health

# FAB 5：SQLA 从 models.sqla.base 导入（不再在包顶层）；indexview 是
# AppBuilder 的构造参数（init_app 不再收它）。
db = SQLA()
appbuilder = AppBuilder(indexview=DashboardIndexView)


def create_app(config_object: str = "config") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    with app.app_context():
        appbuilder.init_app(app, db.session)
        db.create_all()

    # 健康检查挂在 FAB 体系之外：探活不需要登录，也不依赖任何初始化。
    app.add_url_rule("/api/health", "health", health)

    return app
