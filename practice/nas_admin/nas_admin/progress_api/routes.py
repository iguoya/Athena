"""学习进度通用同步 REST API（/api/progress/v1，ADR 0155）。

约定：
- 应用里不认证（主仓库 ADR 0077）：内网直连可信，外网由 Cloudflare Access 在边缘把守。
- 学习者由请求头 `X-Athena-User` 给出（全局目录分配的编号，ADR 0074），暂不校验是否登记。
- 幂等：同一批行重复推送，结果不变（append 忽略已有，lww 比更新时间）。
- 错误一律 JSON `{"error": 代码, "message": 说明}`，不返回堆栈、路径或数据库细节。
"""

from __future__ import annotations

import json
import re
from typing import Any

from flask import Blueprint, Response, current_app, g, jsonify, request
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from nas_admin import access
from nas_admin.driver_api.validate import ValidationError, clean, integer, string
from nas_admin.progress_api import store

bp = Blueprint("progress_api", __name__, url_prefix="/api/progress/v1")

MAX_BODY = 2 * 1024 * 1024  # 一批最多 500 行，每行 JSON 有上限，整体不会超过这个
MAX_ROWS = 500
MAX_DATA = 64 * 1024  # 单行 JSON 序列化后的上限

_APP_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
# 统一成 UTC、毫秒或微秒精度：只有格式一致，字符串比较才等价于时间比较。
_STAMP_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d{1,6})?Z$")


def _error(status: int, code: str, message: str, **extra: Any) -> tuple[Response, int]:
    return jsonify(error=code, message=message, **extra), status


# ---------------------------------------------------------------- 钩子与错误处理


@bp.before_request
def _guard() -> tuple[Response, int] | None:
    if request.content_length and request.content_length > MAX_BODY:
        return _error(413, "too_large", f"请求体不能超过 {MAX_BODY // 1024 // 1024} MB")
    g.address = access.client_address()
    if not access.allow(g.address):
        return _error(429, "rate_limited", "请求太频繁，稍后再试")
    store.ensure_table(store.engine())
    return None


@bp.after_request
def _no_store(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.errorhandler(ValidationError)
def _on_validation(error: ValidationError):
    return _error(400, "invalid", f"{error.field}：{error.message}")


@bp.errorhandler(SQLAlchemyError)
def _on_database(error: SQLAlchemyError):
    current_app.logger.error("progress_api 数据库错误: %s", error)
    if isinstance(error, OperationalError):
        return _error(503, "database_unavailable", "进度库暂不可用")
    return _error(500, "internal", "服务器内部错误")


@bp.errorhandler(HTTPException)
def _on_http(error: HTTPException):
    return _error(error.code or 500, (error.name or "error").lower().replace(" ", "_"), error.description or "")


@bp.errorhandler(Exception)
def _on_unexpected(error: Exception):
    current_app.logger.exception("progress_api 未处理的异常")
    return _error(500, "internal", "服务器内部错误")


# ---------------------------------------------------------------- 校验


def _learner() -> int:
    raw = request.headers.get("X-Athena-User", "").strip()
    if not raw.isdigit():
        raise ValidationError("X-Athena-User", "必须是学习者编号（1～999）")
    return integer(1, 999)("X-Athena-User", int(raw))


def _app_name(field: str, value: Any) -> str:
    text = string(64)(field, value)
    if not _APP_RE.match(text):
        raise ValidationError(field, "应用 id 只能是小写字母、数字和连字符")
    return text


def _table_name(field: str, value: Any) -> str:
    text = string(64)(field, value)
    if not _TABLE_RE.match(text):
        raise ValidationError(field, "表名只能是字母、数字和下划线")
    return text


def _stamp(field: str, value: Any) -> str:
    text = string(40)(field, value)
    if not _STAMP_RE.match(text):
        raise ValidationError(field, "必须是 UTC 的 ISO-8601 时间，形如 2026-10-13T01:02:03.123Z")
    return text


def _mode(field: str, value: Any) -> str:
    if value not in store.MODES:
        raise ValidationError(field, f"必须是 {' / '.join(store.MODES)}")
    return value


def _deleted(field: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value
    raise ValidationError(field, "必须是 true/false")


def _data(field: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(field, "必须是 JSON 对象")
    if len(json.dumps(value, ensure_ascii=False)) > MAX_DATA:
        raise ValidationError(field, f"序列化后不能超过 {MAX_DATA // 1024} KB")
    return value


_ROW_SPEC = {
    "tbl": (_table_name, True),
    "pk": (string(400), True),
    "mode": (_mode, True),
    "stamp": (_stamp, True),
    "deleted": (_deleted, False),
    "data": (_data, False),
}


def _row(item: Any) -> dict[str, Any]:
    out = clean(_ROW_SPEC, item)
    out["deleted"] = out.get("deleted", False)
    if not out["deleted"] and "data" not in out:
        raise ValidationError("data", "未删除的行必须带 data")
    out.setdefault("data", None)
    return out


# ---------------------------------------------------------------- 接口


@bp.post("/push")
def push():
    """推一批行。`{"app", "device", "rows": [...]}` → `{accepted, ignored, cursor}`。"""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValidationError("(body)", "请求体必须是 JSON 对象")
    unknown = sorted(set(body) - {"app", "device", "rows"})
    if unknown:
        raise ValidationError(unknown[0], "未知字段")
    app_id = _app_name("app", body.get("app"))
    device = string(64)("device", body.get("device"))
    items = body.get("rows")
    if not isinstance(items, list):
        raise ValidationError("rows", "必须是数组")
    if len(items) > MAX_ROWS:
        raise ValidationError("rows", f"一批最多 {MAX_ROWS} 行")
    cleaned = [_row(item) for item in items]
    learner = _learner()
    with store.engine().begin() as conn:
        result = store.push(conn, learner, app_id, device, cleaned)
    current_app.logger.info(
        "progress_api push from=%s learner=%s app=%s rows=%d accepted=%d",
        g.address,
        learner,
        app_id,
        len(cleaned),
        result["accepted"],
    )
    return jsonify(**result)


@bp.get("/pull")
def pull():
    """拉序号大于 `since` 的行：`?app=…&since=0&limit=500` → `{rows, next, more}`。"""
    app_id = _app_name("app", request.args.get("app"))
    try:
        since = int(request.args.get("since", "0"))
        limit = int(request.args.get("limit", str(MAX_ROWS)))
    except ValueError:
        raise ValidationError("since/limit", "必须是整数") from None
    since = integer(0, 2**62)("since", since)
    limit = integer(1, MAX_ROWS)("limit", limit)
    learner = _learner()
    with store.engine().connect() as conn:
        result = store.pull(conn, learner, app_id, since, limit)
    return jsonify(**result)
