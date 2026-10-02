"""驾考进度的网页只读仪表盘（ADR 0069）。

给人看的页面，和给设备用的 REST API（driver_api）是两条通道：这里免设备令牌、
只读、只做聚合统计，访问边界由 Cloudflare Access（外网）与内网信任域兜底。
"""

from __future__ import annotations

from flask import Flask


def init_driver_dashboard(app: Flask) -> None:
    from nas_admin.driver_dashboard.routes import bp

    app.register_blueprint(bp)
