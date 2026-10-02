"""请求体校验：每个字段都有类型、长度、范围，未知字段一律拒绝。

不引入新依赖，规则写在一处，报错指到字段名。拒绝未知字段是有意的：客户端字段名
写错时立刻 400，而不是悄悄丢数据。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Mapping

MAX_TEXT = 8000  # 正文类字段（笔记、JSON 串）上限
MAX_ID = 200  # 题号、点位号、键这类短标识上限


class ValidationError(ValueError):
    """校验失败；`field` 指出是哪个字段。"""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message


Check = Callable[[str, Any], Any]


def string(max_length: int = MAX_ID, *, allow_empty: bool = False) -> Check:
    def check(field: str, value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError(field, "必须是字符串")
        if not allow_empty and not value.strip():
            raise ValidationError(field, "不能为空")
        if len(value) > max_length:
            raise ValidationError(field, f"长度不能超过 {max_length}")
        if "\x00" in value:
            raise ValidationError(field, "不能含空字符")
        return value

    return check


def integer(low: int, high: int) -> Check:
    def check(field: str, value: Any) -> int:
        # bool 是 int 的子类，True/False 不当整数收。
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(field, "必须是整数")
        if not low <= value <= high:
            raise ValidationError(field, f"必须在 {low}～{high} 之间")
        return value

    return check


def flag() -> Check:
    """布尔旗标：客户端存的是 0/1，也接受 true/false。"""

    def check(field: str, value: Any) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int) and value in (0, 1):
            return value
        raise ValidationError(field, "必须是 0/1 或 true/false")

    return check


def iso_time() -> Check:
    """ISO-8601 时间串，原样保存（不转时区、不改精度）。

    客户端写的是本机本地时间（不带时区），应用层只做字符串比较；服务端不替它
    改写，否则同一条记录两端字符串不一致，按「题号+时间」去重就失效。
    """

    def check(field: str, value: Any) -> str:
        if not isinstance(value, str) or not value or len(value) > 40:
            raise ValidationError(field, "必须是 ISO-8601 时间字符串")
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValidationError(field, "不是合法的 ISO-8601 时间") from None
        return value

    return check


def clean(spec: Mapping[str, tuple[Check, bool]], raw: Any) -> dict[str, Any]:
    """按 spec 校验一条记录。spec: 字段名 -> (校验函数, 是否必填)。"""
    if not isinstance(raw, dict):
        raise ValidationError("(item)", "必须是 JSON 对象")
    unknown = sorted(set(raw) - set(spec))
    if unknown:
        raise ValidationError(unknown[0], "未知字段")
    out: dict[str, Any] = {}
    for name, (check, required) in spec.items():
        if name not in raw or raw[name] is None:
            if required:
                raise ValidationError(name, "必填")
            continue
        out[name] = check(name, raw[name])
    return out
