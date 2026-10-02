"""驾考进度库的表结构工具（ADR 0070 决策 6、ADR 0071）：全新建库 + 加 user 列。

在能连中心库的机器上以**属主**身份跑（API 用的低权限角色没有 DDL，ADR 0068 决策 6）：

    python3 scripts/driver_migrate_users.py postgresql://athena_driver:密码@192.168.6.1:5432/athena_driver

幂等，重复跑没有副作用，对三种库况都收敛到同一结构：

- 空库：按现行结构（ADR 0071，含 user 列）建全部表——这是 ADR 0070「表结构管理
  移交服务端」后全新部署的初始化入口，替代旧的「客户端在内网首连建表」。
- 已有表、没有 user 列（0071 之前）：各表加 `user TEXT NOT NULL DEFAULT 'tiger'`
  （存量记录全归首用户），achievements / exam_drafts 的主键换成 (user, key)。
- 已是新结构：什么都不做。

表结构与 `subjects/driver/lib/progress.dart` 的本地建表保持同名同列（0070）；时间列
沿用 ISO 字符串存 TEXT，去重靠 API 层「先查再插」（ADR 0068），中心表不建业务键
唯一索引——与 0067 时代迁入的存量表一致。
"""

from __future__ import annotations

import sys

import psycopg

FIRST_USER = "tiger"

# 事件表：id 全库自增（拉取游标）；列定义与客户端本地 SQLite 一致（除方言差异）。
_ID = "id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
_EVENT_TABLES = {
    "attempts": """
        question_id TEXT NOT NULL, topic_id TEXT NOT NULL, subject_id TEXT NOT NULL,
        correct INTEGER NOT NULL, duration_ms INTEGER NOT NULL DEFAULT 0,
        hesitant INTEGER NOT NULL DEFAULT 0, at TEXT NOT NULL""",
    "exams": "subject_id TEXT NOT NULL, score INTEGER NOT NULL, passed INTEGER NOT NULL, at TEXT NOT NULL",
    "notices": "kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL, at TEXT NOT NULL, read INTEGER NOT NULL",
    "drill_runs": "item_id TEXT NOT NULL, mistakes TEXT NOT NULL, at TEXT NOT NULL",
    "point_notes": "item_id TEXT NOT NULL, step INTEGER NOT NULL, text TEXT NOT NULL, at TEXT NOT NULL",
    "rehearsals": "item_id TEXT NOT NULL, missed TEXT NOT NULL, total INTEGER NOT NULL, at TEXT NOT NULL",
    "drill_notes": "item_id TEXT NOT NULL, text TEXT NOT NULL, at TEXT NOT NULL",
}
# 键表：主键含 user（ADR 0071）。
_KEY_TABLES = {
    "achievements": "at TEXT NOT NULL",
    "exam_drafts": """
        subject_id TEXT NOT NULL, title TEXT NOT NULL, question_ids TEXT NOT NULL,
        question_count INTEGER NOT NULL, minutes INTEGER NOT NULL, pass_score INTEGER NOT NULL,
        points_per_question INTEGER NOT NULL, mix TEXT NOT NULL, full_bank INTEGER NOT NULL,
        picked TEXT NOT NULL, started_at TEXT NOT NULL, saved_at TEXT""",
}
# 键表的键列名（主键 = user + 这个列）。
_KEY_COLUMN = {"achievements": "key", "exam_drafts": "draft_key"}


def column_exists(conn: psycopg.Connection, table: str, column: str) -> bool:
    found = conn.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
        (table, column),
    ).fetchone()
    return found is not None


def table_exists(conn: psycopg.Connection, table: str) -> bool:
    found = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,)).fetchone()
    return found is not None


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    url = sys.argv[1]
    with psycopg.connect(url) as conn:
        for table, columns in _EVENT_TABLES.items():
            if not table_exists(conn, table):
                # DDL 的 DEFAULT 不接受绑定参数；FIRST_USER 是本模块常量，无注入面。
                conn.execute(f"CREATE TABLE {table} ({_ID}, \"user\" TEXT NOT NULL DEFAULT '{FIRST_USER}', {columns})")
                print(f"[建表] {table}（新结构，含 user）")
                continue
            if column_exists(conn, table, "user"):
                print(f"[跳过] {table} 已是新结构")
                continue
            conn.execute(f"ALTER TABLE {table} ADD COLUMN \"user\" TEXT NOT NULL DEFAULT '{FIRST_USER}'")
            print(f"[加列] {table}.user DEFAULT '{FIRST_USER}'")
        for table, columns in _KEY_TABLES.items():
            key = _KEY_COLUMN[table]
            if not table_exists(conn, table):
                conn.execute(
                    f"CREATE TABLE {table} (\"user\" TEXT NOT NULL DEFAULT '{FIRST_USER}', {key} TEXT NOT NULL, {columns},"
                    f" PRIMARY KEY (\"user\", {key}))"
                )
                print(f"[建表] {table}（新结构，主键 (user, {key})）")
                continue
            if column_exists(conn, table, "user"):
                print(f"[跳过] {table} 已是新结构")
                continue
            # 单用户存量里键本来就唯一，直接把主键换成 (user, 键) 不涉及数据变更。
            conn.execute(f"ALTER TABLE {table} ADD COLUMN \"user\" TEXT NOT NULL DEFAULT '{FIRST_USER}'")
            conn.execute(f"ALTER TABLE {table} DROP CONSTRAINT {table}_pkey")
            conn.execute(f'ALTER TABLE {table} ADD PRIMARY KEY ("user", {key})')
            print(f"[升级] {table}: 加 user 列，主键 -> (user, {key})")
        conn.commit()
    print("完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
