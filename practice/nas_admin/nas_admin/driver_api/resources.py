"""追加型资源的字段规则与去重键。

这些记录产生后不再修改（只追加），两台机器各自产生的记录取并集即可，没有合并冲突。
**去重键**决定幂等：同一条记录重复上传不会重复入库。键沿用旧同步的约定——题号加时间
（driver ADR 0010），客户端的 `at` 是毫秒精度的时间串，同一条记录两端字符串一致。

库里的 `id` 是服务端自增，只用于增量拉取的游标（`after_id`），客户端不要拿它当全局
标识：家里直连写入的记录和 API 写入的记录共用同一个序列。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from sqlalchemy import Table

from nas_admin.driver_api import schema
from nas_admin.driver_api.validate import (
    MAX_ID,
    MAX_TEXT,
    Check,
    flag,
    integer,
    iso_time,
    string,
)

# 单次耗时上限：24 小时，足够覆盖挂起后恢复的最长场景，挡住明显的垃圾值。
_MAX_MS = 24 * 3600 * 1000


@dataclass(frozen=True)
class Resource:
    path: str  # URL 段，如 "drill-runs"
    table: Table
    fields: Mapping[str, tuple[Check, bool]]  # 字段 -> (校验, 必填)
    dedupe: tuple[str, ...]  # 去重键（列名）


APPEND_ONLY: dict[str, Resource] = {
    r.path: r
    for r in (
        Resource(
            "attempts",
            schema.attempts,
            {
                "question_id": (string(), True),
                "topic_id": (string(), True),
                "subject_id": (string(), True),
                "correct": (flag(), True),
                "duration_ms": (integer(0, _MAX_MS), False),
                "hesitant": (flag(), False),
                "at": (iso_time(), True),
                # 场合标记（driver ADR 0057）：可缺省，旧客户端不传按平时练习。
                "kind": (string(MAX_ID), False),
            },
            ("user", "question_id", "at"),
        ),
        Resource(
            "exams",
            schema.exams,
            {
                "subject_id": (string(), True),
                "score": (integer(0, 1000), True),
                "passed": (flag(), True),
                "at": (iso_time(), True),
            },
            ("user", "subject_id", "at"),
        ),
        Resource(
            "drill-runs",
            schema.drill_runs,
            {
                "item_id": (string(), True),
                "mistakes": (string(MAX_TEXT, allow_empty=True), True),
                "at": (iso_time(), True),
            },
            ("user", "item_id", "at"),
        ),
        Resource(
            "rehearsals",
            schema.rehearsals,
            {
                "item_id": (string(), True),
                "missed": (string(MAX_TEXT, allow_empty=True), True),
                "total": (integer(0, 10_000), True),
                "at": (iso_time(), True),
            },
            ("user", "item_id", "at"),
        ),
        Resource(
            "drill-notes",
            schema.drill_notes,
            {
                "item_id": (string(), True),
                "text": (string(MAX_TEXT, allow_empty=True), True),
                "at": (iso_time(), True),
            },
            ("user", "item_id", "at"),
        ),
        Resource(
            "point-notes",
            schema.point_notes,
            {
                "item_id": (string(), True),
                "step": (integer(0, 1000), True),
                "text": (string(MAX_TEXT, allow_empty=True), True),
                "at": (iso_time(), True),
            },
            ("user", "item_id", "step", "at"),
        ),
        Resource(
            "notices",
            schema.notices,
            {
                "kind": (string(MAX_ID), True),
                "title": (string(MAX_ID), True),
                "body": (string(MAX_TEXT, allow_empty=True), True),
                "at": (iso_time(), True),
                "read": (flag(), False),
            },
            ("user", "kind", "title", "at"),
        ),
    )
}

# exam_drafts：整份可变，按键覆盖（见 routes）。
DRAFT_FIELDS: Mapping[str, tuple[Check, bool]] = {
    "subject_id": (string(), True),
    "title": (string(MAX_ID), True),
    "question_ids": (string(MAX_TEXT), True),
    "question_count": (integer(0, 1000), True),
    "minutes": (integer(0, 1000), True),
    "pass_score": (integer(0, 1000), True),
    "points_per_question": (integer(0, 100), True),
    "mix": (string(MAX_TEXT, allow_empty=True), True),
    "full_bank": (flag(), True),
    "picked": (string(MAX_TEXT, allow_empty=True), True),
    "started_at": (iso_time(), True),
    "saved_at": (iso_time(), False),
}
