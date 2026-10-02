"""驾考（driver）进度库的表结构镜像。

**真正的表由 driver 客户端在内网首次连接时建好**（`subjects/driver/lib/progress.dart`
的 `_ensureSchema`），本 API 的数据库角色没有 DDL 权限，也不建表——这样「家里直连」
和「外网走 API」读写的是同一份数据。这里只镜像列定义，用途两个：

1. 用 SQLAlchemy Core 构造查询，不手拼 SQL（防注入的底线）。
2. 测试里在 SQLite 上建同构的表。

列名、类型必须和 progress.dart 一致；时间列沿用 ISO 字符串存 TEXT（应用层只做字符串
比较，不依赖数据库时区，跨机器也不受服务器时区影响）。
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, Integer, MetaData, Table, Text

metadata = MetaData()

# PG 里是 BIGINT IDENTITY；SQLite 只有 INTEGER PRIMARY KEY 才自增。
_ID = BigInteger().with_variant(Integer, "sqlite")


def _table(name: str, *columns: Column) -> Table:
    return Table(name, metadata, Column("id", _ID, primary_key=True, autoincrement=True), *columns)


attempts = _table(
    "attempts",
    Column("question_id", Text, nullable=False),
    Column("topic_id", Text, nullable=False),
    Column("subject_id", Text, nullable=False),
    Column("correct", Integer, nullable=False),
    Column("duration_ms", Integer, nullable=False, server_default="0"),
    Column("hesitant", Integer, nullable=False, server_default="0"),
    Column("at", Text, nullable=False),
)

exams = _table(
    "exams",
    Column("subject_id", Text, nullable=False),
    Column("score", Integer, nullable=False),
    Column("passed", Integer, nullable=False),
    Column("at", Text, nullable=False),
)

notices = _table(
    "notices",
    Column("kind", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("body", Text, nullable=False),
    Column("at", Text, nullable=False),
    Column("read", Integer, nullable=False),
)

achievements = Table(
    "achievements",
    metadata,
    Column("key", Text, primary_key=True),
    Column("at", Text, nullable=False),
)

exam_drafts = Table(
    "exam_drafts",
    metadata,
    Column("draft_key", Text, primary_key=True),
    Column("subject_id", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("question_ids", Text, nullable=False),
    Column("question_count", Integer, nullable=False),
    Column("minutes", Integer, nullable=False),
    Column("pass_score", Integer, nullable=False),
    Column("points_per_question", Integer, nullable=False),
    Column("mix", Text, nullable=False),
    Column("full_bank", Integer, nullable=False),
    Column("picked", Text, nullable=False),
    Column("started_at", Text, nullable=False),
    Column("saved_at", Text),
)

drill_runs = _table(
    "drill_runs",
    Column("item_id", Text, nullable=False),
    Column("mistakes", Text, nullable=False),
    Column("at", Text, nullable=False),
)

point_notes = _table(
    "point_notes",
    Column("item_id", Text, nullable=False),
    Column("step", Integer, nullable=False),
    Column("text", Text, nullable=False),
    Column("at", Text, nullable=False),
)

rehearsals = _table(
    "rehearsals",
    Column("item_id", Text, nullable=False),
    Column("missed", Text, nullable=False),
    Column("total", Integer, nullable=False),
    Column("at", Text, nullable=False),
)

drill_notes = _table(
    "drill_notes",
    Column("item_id", Text, nullable=False),
    Column("text", Text, nullable=False),
    Column("at", Text, nullable=False),
)

# point_photos 暂不开放（照片是文件，体积大，v1 只同步文字数据）。
