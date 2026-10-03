"""驾考进度仪表盘的路由（ADR 0069）：页面与聚合数据端点，均免登录、只读。

为什么免登录可以：外网前面有 Cloudflare Access（www.yatiger.cn 现有策略），内网是
家庭信任域；这里的「门」不在这层应用上。也正因为免登录，错误响应只给结论不给细节
（不返回堆栈、路径、数据库信息），且响应一律 no-store——个人数据不进任何中间层缓存。
"""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError

from nas_admin.driver_api import store
from nas_admin.driver_dashboard import aggregates, diagnosis

bp = Blueprint("driver_dashboard", __name__, url_prefix="/driver")


@bp.get("/")
def index():
    return render_template("driver_dashboard.html")


@bp.get("/data.json")
def data():
    payload = aggregates.collect()
    payload["overview"]["streak"] = aggregates.day_streak(payload["daily"])
    payload["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    return jsonify(payload)


@bp.get("/diagnosis.json")
def diagnosis_data():
    """学习诊断：按单个学习者算（遗忘、错因是「这个人」的事）。不带 user 默认作答最多的那位。"""
    people = diagnosis.learners()
    if not people:
        return jsonify(learners=[], selected=None, diagnosis=None)
    wanted = request.args.get("user")
    known = {p["id"] for p in people}
    if wanted is not None and wanted not in known:
        return jsonify(error="unknown_learner", message="没有这位学习者的作答记录"), 404
    selected = wanted or people[0]["id"]
    return jsonify(
        learners=people,
        selected=selected,
        diagnosis=diagnosis.build(diagnosis.attempts_of(selected), aggregates.TOPIC_TITLES),
        generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
    )


@bp.after_request
def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.errorhandler(store.NotConfigured)
def _on_not_configured(error: store.NotConfigured):
    current_app.logger.error("driver_dashboard: %s", error)
    return jsonify(error="not_configured", message="进度数据库尚未配置"), 503


@bp.errorhandler(SQLAlchemyError)
def _on_database(error: SQLAlchemyError):
    current_app.logger.error("driver_dashboard 数据库错误: %s", error)
    if isinstance(error, OperationalError):
        return jsonify(error="database_unavailable", message="进度数据库暂不可用"), 503
    if isinstance(error, DBAPIError) and getattr(getattr(error, "orig", None), "sqlstate", None) == "42P01":
        return jsonify(error="not_initialized", message="进度库尚未初始化：需先在内网用驾考客户端连接一次以建表"), 503
    return jsonify(error="internal", message="服务器内部错误"), 500
