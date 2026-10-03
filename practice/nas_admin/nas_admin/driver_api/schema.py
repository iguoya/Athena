"""驾考（driver）进度库的表结构镜像。

**真正的表由 driver 客户端在内网首次连接时建好**（`subjects/driver/lib/progress.dart`
的 `_ensureSchema`），本 API 的数据库角色没有 DDL 权限，也不建表——这样「家里直连」
和「外网走 API」读写的是同一份数据。这里只镜像列定义，用途两个：

1. 用 SQLAlchemy Core 构造查询，不手拼 SQL（防注入的底线）。
2. 测试里在 SQLite 上建同构的表。

列名、类型必须和 progress.dart 一致；时间列沿用 ISO 字符串存 TEXT（应用层只做字符串
比较，不依赖数据库时区，跨机器也不受服务器时区影响）。

每张表都带 `user` 列（ADR 0071）：同一份题库给多个学习者用，个人数据按用户隔离。
列带 DEFAULT 'tiger' 只为让不带该列的测试 fixture 仍能建数据；真实读写永远显式给值。
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, Integer, MetaData, Table, Text

metadata = MetaData()

# PG 里是 BIGINT IDENTITY；SQLite 只有 INTEGER PRIMARY KEY 才自增。
_ID = BigInteger().with_variant(Integer, "sqlite")

# 首用户名（ADR 0071）：加列时的默认值，存量数据全归它。
FIRST_USER = "tiger"


def _table(name: str, *columns: Column) -> Table:
    return Table(
        name,
        metadata,
        Column("id", _ID, primary_key=True, autoincrement=True),
        Column("user", Text, nullable=False, server_default=FIRST_USER),
        *columns,
    )


attempts = _table(
    "attempts",
    Column("question_id", Text, nullable=False),
    Column("topic_id", Text, nullable=False),
    Column("subject_id", Text, nullable=False),
    Column("correct", Integer, nullable=False),
    Column("duration_ms", Integer, nullable=False, server_default="0"),
    Column("hesitant", Integer, nullable=False, server_default="0"),
    Column("at", Text, nullable=False),
    # 场合标记（driver ADR 0057）：practice 平时练习 / exam 模拟考；
    # 错题本与考前复习的场景仍在 subject_id（wrong/review），两维正交。
    Column("kind", Text, nullable=False, server_default="practice"),
    # 归因字段（主仓库 ADR 0076）：都可空，旧数据全为空，不参与去重键。
    # chosen 是所选选项的稳定标识（多选排序后逗号拼接）；session_id 是这次作答所属的会话；
    # reason 仅强化练习使用，记这道题为什么被选中。
    Column("chosen", Text),
    Column("session_id", Text),
    Column("reason", Text),
)

exams = _table(
    "exams",
    Column("subject_id", Text, nullable=False),
    Column("score", Integer, nullable=False),
    Column("passed", Integer, nullable=False),
    Column("at", Text, nullable=False),
    # 与该场考试内所有 attempts.session_id 相同，就是「作答属于哪场考试」的关联键；
    # used_ms 是整场实际用时（不含挂起）。（主仓库 ADR 0076）
    Column("session_id", Text),
    Column("used_ms", Integer),
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
    Column("user", Text, primary_key=True, server_default=FIRST_USER),
    Column("key", Text, primary_key=True),
    Column("at", Text, nullable=False),
)

exam_drafts = Table(
    "exam_drafts",
    metadata,
    Column("user", Text, primary_key=True, server_default=FIRST_USER),
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
    # 续答沿用同一个会话（主仓库 ADR 0076 决策 3）。
    Column("session_id", Text),
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

# 答错后看解析的停留（主仓库 ADR 0076 决策 4）：作答在判定时刻写入，停留在之后才知道，
# 回头改作答行会破坏追加型同步，所以单独成一个事件，按 (question_id, attempt_at) 对上那次作答。
explain_views = _table(
    "explain_views",
    Column("question_id", Text, nullable=False),
    Column("attempt_at", Text, nullable=False),
    Column("dwell_ms", Integer, nullable=False),
)

# point_photos 暂不开放（照片是文件，体积大，v1 只同步文字数据）。
