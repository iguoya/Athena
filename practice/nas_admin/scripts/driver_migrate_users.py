"""驾考进度库的表结构工具（ADR 0070 决策 6、0071、0073、0075）：全新建库、加 user 列、
tiger 收编为数字编号、全局用户目录登记。

在能连中心库的机器上以**属主**身份跑（API 用的低权限角色没有 DDL，ADR 0068 决策 6）：

    python3 scripts/driver_migrate_users.py \
        postgresql://athena_driver:密码@192.168.6.1:5432/athena_driver \
        [--users-db postgresql://属主:密码@192.168.6.1:5432/nas_admin]

幂等，重复跑没有副作用，对各种库况都收敛到同一状态：

- 空库：按现行结构（ADR 0071，含 user 列）建全部表——这是 ADR 0070「表结构管理
  移交服务端」后全新部署的初始化入口。
- 已有表、没有 user 列（0071 之前）：各表加 user 列（DEFAULT 为 tiger 的编号），
  achievements / exam_drafts 的主键换成 (user, key)。
- 加列时默认值是 'tiger' 的库（0071 时代的中间状态），或曾被收编成 `u_…` 的库
  （0073 时代，从未随发行版发出）：全部表里这些旧值的 `user` 行 UPDATE 为数字编号，
  列 DEFAULT 一并改写——旧直连客户端继续写入也落到正确归属。
- `attempts` 没有 `kind` 列（driver ADR 0057 之前的库）：补上，默认 `practice`；不回填历史。
- 归因列（主仓库 ADR 0076）：`attempts.chosen/session_id/reason`、`exams.session_id/used_ms`、
  `exam_drafts.session_id` 都是可空列，缺则补；新表 `explain_views` 缺则建。老数据这些列为空，不回填。
- 已收编（DEFAULT 已是数字编号）：什么都不做。

tiger 的编号（ADR 0075，服务端分配的纯数字，1～999）：`--tiger-id` 显式给；否则先试着
从全局用户目录或列 DEFAULT 里找回（重复跑保持一致），再不成就取目录里下一个空号
（空目录是 1）。登录时输入名字 tiger 即可，重名才会问编号，所以不再需要人工分发。

`--users-db` 指向后台库（nas_admin）时登记全局用户目录 `athena_users`（ADR 0073 决策 2、
ADR 0075）；不给就跳过登记（只做 driver 库）。

表结构与 `subjects/driver/lib/progress.dart` 的本地建表保持同名同列（0070）；时间列
沿用 ISO 字符串存 TEXT，去重靠 API 层「先查再插」（ADR 0068），中心表不建业务键
唯一索引——与 0067 时代迁入的存量表一致。
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone

import psycopg

FIRST_USER = "tiger"
MAX_ID = 999  # 与 nas_admin/user_api/directory.py 一致

# 事件表：id 全库自增（拉取游标）；列定义与客户端本地 SQLite 一致（除方言差异）。
_ID = "id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
_EVENT_TABLES = {
    "attempts": """
        question_id TEXT NOT NULL, topic_id TEXT NOT NULL, subject_id TEXT NOT NULL,
        correct INTEGER NOT NULL, duration_ms INTEGER NOT NULL DEFAULT 0,
        hesitant INTEGER NOT NULL DEFAULT 0, at TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'practice'""",
    "exams": "subject_id TEXT NOT NULL, score INTEGER NOT NULL, passed INTEGER NOT NULL, at TEXT NOT NULL",
    "notices": "kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL, at TEXT NOT NULL, read INTEGER NOT NULL",
    "drill_runs": "item_id TEXT NOT NULL, mistakes TEXT NOT NULL, at TEXT NOT NULL",
    "point_notes": "item_id TEXT NOT NULL, step INTEGER NOT NULL, text TEXT NOT NULL, at TEXT NOT NULL",
    "rehearsals": "item_id TEXT NOT NULL, missed TEXT NOT NULL, total INTEGER NOT NULL, at TEXT NOT NULL",
    "drill_notes": "item_id TEXT NOT NULL, text TEXT NOT NULL, at TEXT NOT NULL",
    # 答错后看解析的停留（主仓库 ADR 0076 决策 4）
    "explain_views": "question_id TEXT NOT NULL, attempt_at TEXT NOT NULL, dwell_ms INTEGER NOT NULL",
}
# 可空的归因列（主仓库 ADR 0076）：新建库和老库都用 ADD COLUMN IF NOT EXISTS 补齐，幂等。
_OPTIONAL_COLUMNS = {
    "attempts": [("chosen", "TEXT"), ("session_id", "TEXT"), ("reason", "TEXT")],
    "exams": [("session_id", "TEXT"), ("used_ms", "INTEGER")],
    "exam_drafts": [("session_id", "TEXT")],
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

ALL_TABLES = [*_EVENT_TABLES, *_KEY_TABLES]


def table_exists(conn: psycopg.Connection, table: str) -> bool:
    found = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_name = %s", (table,)).fetchone()
    return found is not None


def column_exists(conn: psycopg.Connection, table: str, column: str) -> bool:
    found = conn.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
        (table, column),
    ).fetchone()
    return found is not None


def user_default(conn: psycopg.Connection, table: str) -> str | None:
    """user 列当前的 DEFAULT（去掉 PG 的 ::text 造型与引号），没有则 None。"""
    raw = conn.execute(
        "SELECT column_default FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = 'user'",
        (table,),
    ).fetchone()
    if raw is None or raw[0] is None:
        return None
    value = str(raw[0]).split("::")[0].strip().strip("'")
    return value or None


def valid_id(value: str) -> bool:
    """学习者编号：1～999 的纯数字串（ADR 0075 决策 1）。"""
    return re.fullmatch(r"[0-9]{1,3}", value) is not None and 1 <= int(value) <= MAX_ID


def directory_exists(users: psycopg.Connection) -> bool:
    return table_exists(users, "athena_users")


def ensure_directory(users: psycopg.Connection) -> None:
    """建全局用户目录（结构同 user_api/directory.py）。

    0073 时代的草稿结构是 `id TEXT`、从未随发行版发出：表空就重建，有数据就停下来让人看，
    不替人改写不认识的数据。
    """
    if directory_exists(users):
        kind = users.execute(
            "SELECT data_type FROM information_schema.columns WHERE table_name = 'athena_users' AND column_name = 'id'"
        ).fetchone()
        if kind and kind[0] != "integer":
            if users.execute("SELECT count(*) FROM athena_users").fetchone()[0]:
                raise SystemExit("athena_users 是旧结构（id 不是整数）且已有数据，请先人工检查再处理。")
            users.execute("DROP TABLE athena_users")
            print("[目录] 丢弃空的旧结构 athena_users")
    users.execute(
        "CREATE TABLE IF NOT EXISTS athena_users ("
        "  id INTEGER PRIMARY KEY,"
        "  name TEXT NOT NULL,"
        "  name_key TEXT NOT NULL,"
        "  created_at TEXT NOT NULL,"
        "  updated_at TEXT NOT NULL"
        ")"
    )
    users.execute("CREATE INDEX IF NOT EXISTS athena_users_name_key ON athena_users (name_key)")


def find_tiger_id(conn: psycopg.Connection, users_url: str | None, explicit: str | None) -> str:
    """tiger 编号的确定顺序：显式给 > 用户目录里已有的 > 列 DEFAULT（已收编的库）> 目录里下一个空号。"""
    if explicit:
        if not valid_id(explicit):
            raise SystemExit(f"--tiger-id 必须是 1～{MAX_ID} 的数字：{explicit!r}")
        return explicit
    if users_url:
        with psycopg.connect(users_url) as users:
            if directory_exists(users):
                ensure_directory(users)  # 兼容旧结构：空表会被重建，随后下面按新结构查
                found = users.execute("SELECT id FROM athena_users WHERE name_key = %s", (FIRST_USER,)).fetchone()
                if found:
                    return str(found[0])
            users.commit()
    for table in ALL_TABLES:
        if table_exists(conn, table) and column_exists(conn, table, "user"):
            value = user_default(conn, table)
            if value and value != FIRST_USER and valid_id(value):
                return value  # 收编过的库：DEFAULT 已是数字编号
    if users_url:
        with psycopg.connect(users_url) as users:
            ensure_directory(users)
            top = users.execute("SELECT coalesce(max(id), 0) FROM athena_users").fetchone()[0]
            users.commit()
        chosen = str(int(top) + 1)
    else:
        chosen = "1"
    if not valid_id(chosen):
        raise SystemExit(f"学习者编号已用到 {MAX_ID}，无法再分配")
    print(f"[编号] tiger 的学习者编号：{chosen}")
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="driver 库的属主连接串")
    parser.add_argument("--tiger-id", help="显式指定 tiger 的学习者编号（默认自动找回或分配）")
    parser.add_argument("--users-db", help="后台库连接串：登记全局用户目录 athena_users")
    args = parser.parse_args()

    with psycopg.connect(args.url) as conn:
        tiger_id = find_tiger_id(conn, args.users_db, args.tiger_id)
        for table, columns in _EVENT_TABLES.items():
            if not table_exists(conn, table):
                # DDL 的 DEFAULT 不接受绑定参数；tiger_id 已过 valid_id（纯数字）再内插，无注入面。
                conn.execute(
                    f"CREATE TABLE {table} ({_ID}, \"user\" TEXT NOT NULL DEFAULT '{tiger_id}', {columns})"
                )
                print(f"[建表] {table}（含 user 列）")
                continue
            if not column_exists(conn, table, "user"):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN \"user\" TEXT NOT NULL DEFAULT '{FIRST_USER}'")
                print(f"[加列] {table}.user")
        # 场合标记（driver ADR 0057）：老库没有就补上，默认平时练习。历史作答的 exam 回填不在这里做。
        if table_exists(conn, "attempts") and not column_exists(conn, "attempts", "kind"):
            conn.execute("ALTER TABLE attempts ADD COLUMN kind TEXT NOT NULL DEFAULT 'practice'")
            print("[加列] attempts.kind")
        for table, columns in _KEY_TABLES.items():
            key = _KEY_COLUMN[table]
            if not table_exists(conn, table):
                conn.execute(
                    f"CREATE TABLE {table} (\"user\" TEXT NOT NULL DEFAULT '{tiger_id}', {key} TEXT NOT NULL,"
                    f" {columns}, PRIMARY KEY (\"user\", {key}))"
                )
                print(f"[建表] {table}（主键 (user, {key})）")
                continue
            if not column_exists(conn, table, "user"):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN \"user\" TEXT NOT NULL DEFAULT '{FIRST_USER}'")
                conn.execute(f"ALTER TABLE {table} DROP CONSTRAINT {table}_pkey")
                conn.execute(f'ALTER TABLE {table} ADD PRIMARY KEY ("user", {key})')
                print(f"[升级] {table}: 加 user 列，主键 -> (user, {key})")
        for table, extra in _OPTIONAL_COLUMNS.items():
            if not table_exists(conn, table):
                continue
            for name, kind in extra:
                if not column_exists(conn, table, name):
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {kind}")
                    print(f"[加列] {table}.{name}（ADR 0076）")
        # 收编（ADR 0075）：字面量 tiger 和 0073 时代的 `u_…` 编号，全部换算成数字编号。
        adopted = user_default(conn, "attempts")
        if adopted != tiger_id:
            legacy = [FIRST_USER]
            if adopted and adopted != FIRST_USER and not valid_id(adopted):
                legacy.append(adopted)
            with conn.transaction():
                for table in ALL_TABLES:
                    if not table_exists(conn, table) or not column_exists(conn, table, "user"):
                        continue
                    moved = conn.execute(
                        f'UPDATE {table} SET "user" = %s WHERE "user" = ANY(%s)', (tiger_id, legacy)
                    ).rowcount
                    # SET DEFAULT 不接受绑定参数；tiger_id 已过 valid_id 白名单。
                    conn.execute(f"ALTER TABLE {table} ALTER COLUMN \"user\" SET DEFAULT '{tiger_id}'")
                    if moved:
                        print(f"[收编] {table}: {moved} 行 {legacy} -> {tiger_id}")
            print(f"[收编] 各表 user 列 DEFAULT -> {tiger_id}")
        else:
            print("[跳过] 已按数字编号收编过")
        conn.commit()

    if args.users_db:
        with psycopg.connect(args.users_db) as users:
            ensure_directory(users)
            taken = users.execute("SELECT name_key FROM athena_users WHERE id = %s", (int(tiger_id),)).fetchone()
            if taken and taken[0] != FIRST_USER:
                raise SystemExit(f"编号 {tiger_id} 已被别的学习者占用：{taken[0]!r}")
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            users.execute(
                "INSERT INTO athena_users (id, name, name_key, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)"
                " ON CONFLICT (id) DO NOTHING",
                (int(tiger_id), FIRST_USER, FIRST_USER, now, now),
            )
            users.commit()
            print(f"[目录] athena_users 登记 ({tiger_id}, {FIRST_USER})")
    print("完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
