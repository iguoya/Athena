"""驾考进度 REST API（/api/driver/v1）。

约定：
- 全部接口要设备令牌（`Authorization: Bearer <token>`），没有匿名接口。
- 追加型记录：`POST /<资源>` 批量上传（幂等，重复上传被跳过）；`GET /<资源>?after_id=`
  增量拉取。这两个动作合起来就是同步：上传自己没发出去的，拉取别处新增的。
- 错误一律 JSON `{"error": 代码, "message": 说明}`，不返回堆栈、路径或数据库细节。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, Response, current_app, g, jsonify, request
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from nas_admin.driver_api import auth, store
from nas_admin.driver_api.resources import APPEND_ONLY, DRAFT_FIELDS, Resource
from nas_admin.driver_api.validate import ValidationError, clean, integer, iso_time, string

bp = Blueprint("driver_api", __name__, url_prefix="/api/driver/v1")

MAX_BODY = 1024 * 1024  # 单个请求体上限 1 MB
MAX_BATCH = 500  # 单次批量上传条数
DEFAULT_PAGE = 200
MAX_PAGE = 500


def _error(status: int, code: str, message: str) -> tuple[Response, int]:
    return jsonify(error=code, message=message), status


# ---------------------------------------------------------------- 钩子与错误处理


@bp.before_request
def _guard() -> tuple[Response, int] | None:
    if request.content_length and request.content_length > MAX_BODY:
        return _error(413, "too_large", f"请求体不能超过 {MAX_BODY // 1024} KB")
    device = auth.authenticate(request.headers.get("Authorization"))
    if device is None:
        response, status = _error(401, "unauthorized", "缺少或无效的设备令牌")
        response.headers["WWW-Authenticate"] = 'Bearer realm="driver-api"'
        return response, status
    if not auth.allow(device["id"]):
        return _error(429, "rate_limited", "请求太频繁，稍后再试")
    g.device = device
    return None


@bp.after_request
def _no_store(response: Response) -> Response:
    # 个人数据不该被任何中间层缓存。
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.errorhandler(ValidationError)
def _on_validation(error: ValidationError):
    return _error(400, "invalid", f"{error.field}：{error.message}")


@bp.errorhandler(store.NotConfigured)
def _on_not_configured(error: store.NotConfigured):
    current_app.logger.error("driver_api: %s", error)
    return _error(503, "not_configured", "进度数据库尚未配置")


@bp.errorhandler(SQLAlchemyError)
def _on_database(error: SQLAlchemyError):
    # 细节只进服务端日志；调用者只知道是「库的问题」，不知道库长什么样。
    current_app.logger.error("driver_api 数据库错误: %s", error)
    if isinstance(error, OperationalError):
        return _error(503, "database_unavailable", "进度数据库暂不可用")
    if isinstance(error, DBAPIError) and getattr(getattr(error, "orig", None), "sqlstate", None) == "42P01":
        return _error(503, "not_initialized", "进度库尚未初始化：需先在内网用驾考客户端连接一次以建表")
    return _error(500, "internal", "服务器内部错误")


@bp.errorhandler(HTTPException)
def _on_http(error: HTTPException):
    return _error(error.code or 500, (error.name or "error").lower().replace(" ", "_"), error.description or "")


@bp.errorhandler(Exception)
def _on_unexpected(error: Exception):
    current_app.logger.exception("driver_api 未处理的异常")
    return _error(500, "internal", "服务器内部错误")


# ---------------------------------------------------------------- 工具


def _body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("(body)", "请求体必须是 JSON 对象")
    return data


def _page_args() -> tuple[int, int]:
    def parse(name: str, default: int, low: int, high: int) -> int:
        raw = request.args.get(name)
        if raw is None:
            return default
        try:
            value = int(raw)
        except ValueError:
            raise ValidationError(name, "必须是整数") from None
        return integer(low, high)(name, value)

    return parse("after_id", 0, 0, 2**62), parse("limit", DEFAULT_PAGE, 1, MAX_PAGE)


def _log_write(resource: str, **counts: int) -> None:
    current_app.logger.info("driver_api 写入 device=%s resource=%s %s", g.device["name"], resource, counts)


# ---------------------------------------------------------------- 基础


@bp.get("/ping")
def ping():
    """连通与令牌自检：客户端设置页点「测试连接」用。"""
    return jsonify(ok=True, device=g.device["name"], server_time=datetime.now(timezone.utc).isoformat(timespec="seconds"))


@bp.get("/stats")
def get_stats():
    with store.engine().connect() as conn:
        return jsonify(stats=store.stats(conn))


# ---------------------------------------------------------------- 追加型资源


def _make_list(res: Resource):
    def view():
        after_id, limit = _page_args()
        with store.engine().connect() as conn:
            items, has_more = store.list_after(conn, res, after_id, limit)
        return jsonify(items=items, has_more=has_more, next_after_id=items[-1]["id"] if items else after_id)

    return view


def _make_post(res: Resource):
    def view():
        raw = _body().get("items")
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_BATCH:
            raise ValidationError("items", f"必须是 1～{MAX_BATCH} 条记录的数组")
        # 先全部校验，再开事务写：一条坏数据整批拒绝，不会写到一半。
        items = []
        for index, entry in enumerate(raw):
            try:
                items.append(clean(res.fields, entry))
            except ValidationError as error:
                raise ValidationError(f"items[{index}].{error.field}", error.message) from None
        with store.engine().begin() as conn:
            inserted, skipped = store.insert_missing(conn, res, items)
        _log_write(res.path, inserted=inserted, skipped=skipped)
        return jsonify(inserted=inserted, skipped=skipped)

    return view


for _name, _res in APPEND_ONLY.items():
    bp.add_url_rule(f"/{_name}", endpoint=f"{_name}_list", view_func=_make_list(_res), methods=["GET"])
    bp.add_url_rule(f"/{_name}", endpoint=f"{_name}_post", view_func=_make_post(_res), methods=["POST"])


@bp.post("/notices/read-all")
def notices_read_all():
    with store.engine().begin() as conn:
        updated = store.mark_notices_read(conn)
    _log_write("notices/read-all", updated=updated)
    return jsonify(updated=updated)


# ---------------------------------------------------------------- 成就


@bp.get("/achievements")
def achievements_list():
    with store.engine().connect() as conn:
        return jsonify(items=store.list_achievements(conn))


@bp.put("/achievements/<key>")
def achievements_put(key: str):
    key = string()("key", key)
    at = clean({"at": (iso_time(), True)}, _body())["at"]
    with store.engine().begin() as conn:
        effective = store.put_achievement(conn, key, at)
    _log_write("achievements", key=1)
    return jsonify(key=key, at=effective)


# ---------------------------------------------------------------- 试卷草稿


@bp.get("/exam-drafts/<key>")
def draft_get(key: str):
    key = string()("key", key)
    with store.engine().connect() as conn:
        draft = store.get_draft(conn, key)
    if draft is None:
        return _error(404, "not_found", "没有这份草稿")
    return jsonify(draft)


@bp.put("/exam-drafts/<key>")
def draft_put(key: str):
    key = string()("key", key)
    fields = clean(DRAFT_FIELDS, _body())
    with store.engine().begin() as conn:
        applied = store.put_draft(conn, key, fields)
    _log_write("exam-drafts", applied=int(applied))
    return jsonify(applied=applied)


@bp.delete("/exam-drafts/<key>")
def draft_delete(key: str):
    key = string()("key", key)
    with store.engine().begin() as conn:
        store.delete_draft(conn, key)
    _log_write("exam-drafts", deleted=1)
    return "", 204
