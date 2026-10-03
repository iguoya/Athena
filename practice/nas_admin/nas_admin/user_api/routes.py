"""全局学习者目录 REST API（/api/users/v1，ADR 0074、0075）。

约定：
- 应用里不认证（主仓库 ADR 0077）：内网直连可信，外网由 Cloudflare Access 在边缘把守。
- 学习者无口令：登录就是「名字（重名再加编号）」，接口只告诉你「这个人是几号」。
  没有「列出全部学习者」的接口，按名字查询也不泄露他人编号（ADR 0075 决策 6）。
- 改名只能改自己：请求头 `X-Athena-User` 必须等于被改的编号。无口令模型下这是防
  误操作，不防有意伪造。
- 错误一律 JSON `{"error": 代码, "message": 说明}`，不返回堆栈、路径或数据库细节。
"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, current_app, g, jsonify, request
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from nas_admin import access
from nas_admin.driver_api.validate import ValidationError, clean, integer, string
from nas_admin.user_api import directory

bp = Blueprint("user_api", __name__, url_prefix="/api/users/v1")

MAX_BODY = 4 * 1024  # 这里只有一个名字和一个编号


def _error(status: int, code: str, message: str, **extra: Any) -> tuple[Response, int]:
    return jsonify(error=code, message=message, **extra), status


# ---------------------------------------------------------------- 钩子与错误处理


@bp.before_request
def _guard() -> tuple[Response, int] | None:
    if request.content_length and request.content_length > MAX_BODY:
        return _error(413, "too_large", f"请求体不能超过 {MAX_BODY // 1024} KB")
    g.address = access.client_address()
    if not access.allow(g.address):
        return _error(429, "rate_limited", "请求太频繁，稍后再试")
    directory.ensure_table(directory.engine())
    return None


@bp.after_request
def _no_store(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.errorhandler(ValidationError)
def _on_validation(error: ValidationError):
    return _error(400, "invalid", f"{error.field}：{error.message}")


@bp.errorhandler(directory.DirectoryFull)
def _on_full(error: directory.DirectoryFull):
    return _error(409, "directory_full", str(error))


@bp.errorhandler(SQLAlchemyError)
def _on_database(error: SQLAlchemyError):
    current_app.logger.error("user_api 数据库错误: %s", error)
    if isinstance(error, OperationalError):
        return _error(503, "database_unavailable", "用户目录暂不可用")
    return _error(500, "internal", "服务器内部错误")


@bp.errorhandler(HTTPException)
def _on_http(error: HTTPException):
    return _error(error.code or 500, (error.name or "error").lower().replace(" ", "_"), error.description or "")


@bp.errorhandler(Exception)
def _on_unexpected(error: Exception):
    current_app.logger.exception("user_api 未处理的异常")
    return _error(500, "internal", "服务器内部错误")


# ---------------------------------------------------------------- 工具


def _body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("(body)", "请求体必须是 JSON 对象")
    return data


def _name(field: str, value: Any) -> str:
    """显示名规范与客户端一致：非空、不超过 64 个字符、不含斜杠与空字符。"""
    text = string(directory.MAX_NAME)(field, value).strip()
    if not text:
        raise ValidationError(field, "不能为空")
    if "/" in text or "\\" in text:
        raise ValidationError(field, "不能含斜杠")
    return text


def _user_id(field: str, value: Any) -> int:
    """编号：整数，也接受纯数字串（客户端从本地 JSON 读出来可能是串）。"""
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    return integer(1, directory.MAX_ID)(field, value)


def _acting_user() -> str:
    return request.headers.get("X-Athena-User", "").strip()


def _log(action: str, **fields: Any) -> None:
    current_app.logger.info("user_api %s from=%s %s", action, g.address, fields)


# ---------------------------------------------------------------- 接口


@bp.post("/users")
def register():
    """新建学习者：名字 → 服务端分配编号。重名照样新建，由使用者自己确认（ADR 0075 决策 3）。"""
    fields = clean({"name": (_name, True)}, _body())
    with directory.engine().begin() as conn:
        created = directory.register(conn, fields["name"])
    _log("register", id=created["id"])
    return jsonify(user=created), 201


@bp.post("/login")
def login():
    """按名字登录（ADR 0075 决策 2）。

    - 恰好一个同名学习者 → 200 `{user}`；
    - 没有（或给了编号却对不上）→ 404 `not_found`，两种情况同一个答案，不暗示名字存不存在；
    - 不止一个而没给编号 → 409 `ambiguous` 带匹配个数，客户端再问编号后重发。
    """
    fields = clean({"name": (_name, True), "id": (_user_id, False)}, _body())
    with directory.engine().connect() as conn:
        matches = directory.find(conn, fields["name"], fields.get("id"))
    if not matches:
        return _error(404, "not_found", "没有这个学习者")
    if len(matches) > 1:
        return _error(409, "ambiguous", "有重名的学习者，请再输入学习者编号", matches=len(matches))
    return jsonify(user=matches[0])


def _require_self(user_id: int) -> tuple[Response, int] | None:
    if _acting_user() != str(user_id):
        return _error(403, "forbidden", "只能查看或修改当前登录的学习者自己")
    return None


@bp.get("/users/<int:user_id>")
def get_self(user_id: int):
    """查自己（刷新本机缓存里的名字：别的电脑上改过名这里才看得到）。"""
    denied = _require_self(user_id)
    if denied:
        return denied
    with directory.engine().connect() as conn:
        found = directory.get(conn, user_id)
    if found is None:
        return _error(404, "not_found", "没有这个学习者")
    return jsonify(user=found)


@bp.patch("/users/<int:user_id>")
def rename_self(user_id: int):
    """改自己的名字；改别人的名字被拒绝（ADR 0075 决策 5）。"""
    denied = _require_self(user_id)
    if denied:
        return denied
    fields = clean({"name": (_name, True)}, _body())
    with directory.engine().begin() as conn:
        renamed = directory.rename(conn, user_id, fields["name"])
    if renamed is None:
        return _error(404, "not_found", "没有这个学习者")
    _log("rename", id=user_id)
    return jsonify(user=renamed)
