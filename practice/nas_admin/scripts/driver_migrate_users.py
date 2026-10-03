"""驾考进度库的表结构工具（ADR 0070 决策 6、0071、0073）：全新建库、加 user 列、
tiger 以规范 ID 收编、全局用户目录登记。

在能连中心库的机器上以**属主**身份跑（API 用的低权限角色没有 DDL，ADR 0068 决策 6）：

    python3 scripts/driver_migrate_users.py \
        postgresql://athena_driver:密码@192.168.6.1:5432/athena_driver \
        [--users-db postgresql://属主:密码@192.168.6.1:5432/nas_admin]

幂等，重复跑没有副作用，对各种库况都收敛到同一状态：

- 空库：按现行结构（ADR 0071，含 user 列）建全部表——这是 ADR 0070「表结构管理
  移交服务端」后全新部署的初始化入口。
- 已有表、没有 user 列（0071 之前）：各表加 user 列（DEFAULT 为 tiger 的规范 ID），
  achievements / exam_drafts 的主键换成 (user, key)。
- 加列时默认值是 'tiger' 的库（0071 时代的中间状态）：全部表的 `user='tiger'` 行
  UPDATE 为规范 ID，列 DEFAULT 一并改写——旧直连客户端继续写入也落到正确归属。
- 已收编（DEFAULT 已是规范 ID）：什么都不做。

tiger 的规范 ID（ADR 0073，`u_` + 16 位十六进制）：`--tiger-id` 显式给；否则先试着
从全局用户目录或列 DEFAULT 里找回（重复跑保持一致），再不成就随机生成并**打印**——
在各台电脑的「续用学习者」里输入它（人分发一次，客户端零猜测）。

`--users-db` 指向后台库（nas_admin）时登记全局用户目录 `athena_users(id, name,
created_at)`（ADR 0073 决策 2）；不给就跳过登记（只做 driver 库）。

表结构与 `subjects/driver/lib/progress.dart` 的本地建表保持同名同列（0070）；时间列
沿用 ISO 字符串存 TEXT，去重靠 API 层「先查再插」（ADR 0068），中心表不建业务键
唯一索引——与 0067 时代迁入的存量表一致。
"""

from __future__ import annotations

import argparse
import secrets
import sys
from datetime import datetime, timezone

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


def find_tiger_id(conn: psycopg.Connection, users_url: str | None, explicit: str | None) -> str:
    """tiger 规范 ID 的确定顺序：显式给 > 用户目录里已有的 > 列 DEFAULT > 随机生成。"""
    if explicit:
        return explicit
    if users_url:
        with psycopg.connect(users_url) as users:
            if table_exists(users, "athena_users"):
                found = users.execute("SELECT id FROM athena_users WHERE name = %s", (FIRST_USER,)).fetchone()
                if found:
                    return str(found[0])
    for table in ALL_TABLES:
        if table_exists(conn, table) and column_exists(conn, table, "user"):
            value = user_default(conn, table)
            if value and value != FIRST_USER:
                return value  # 收编过的库：DEFAULT 已是规范 ID
    generated = f"u_{secrets.token_hex(8)}"
    print(f"[ID] tiger 的学习者 ID：{generated}")
    print("     把它记下来——在各台电脑的「续用学习者」里输入，记录就归到这个名下。")
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="driver 库的属主连接串")
    parser.add_argument("--tiger-id", help="显式指定 tiger 的学习者 ID（默认自动生成或找回）")
    parser.add_argument("--users-db", help="后台库连接串：登记全局用户目录 athena_users")
    args = parser.parse_args()

    tiger_id = args.tiger_id
    with psycopg.connect(args.url) as conn:
        if not tiger_id:
            tiger_id = find_tiger_id(conn, args.users_db, args.tiger_id)
        for table, columns in _EVENT_TABLES.items():
            if not table_exists(conn, table):
                # DDL 的 DEFAULT 不接受绑定参数；tiger_id 来自参数或本进程生成，
                # 已按 validate 语义约束为 [A-Za-z0-9_]{1,64} 再内插（无注入面）。
                if not _safe_id(tiger_id):
                    raise SystemExit(f"--tiger-id 含非法字符：{tiger_id!r}")
                conn.execute(
                    f"CREATE TABLE {table} ({_ID}, \"user\" TEXT NOT NULL DEFAULT '{tiger_id}', {columns})"
                )
                print(f"[建表] {table}（含 user 列）")
                continue
            if not column_exists(conn, table, "user"):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN \"user\" TEXT NOT NULL DEFAULT '{FIRST_USER}'")
                print(f"[加列] {table}.user")
        for table, columns in _KEY_TABLES.items():
            key = _KEY_COLUMN[table]
            if not table_exists(conn, table):
                if not _safe_id(tiger_id):
                    raise SystemExit(f"--tiger-id 含非法字符：{tiger_id!r}")
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
        # 收编（ADR 0073）：字面量 tiger 的行与列 DEFAULT 全部换算成规范 ID。
        adopted = user_default(conn, "attempts")
        if adopted != tiger_id:
            if not _safe_id(tiger_id):
                raise SystemExit(f"tiger ID 含非法字符：{tiger_id!r}")
            with conn.transaction():
                for table in ALL_TABLES:
                    if not table_exists(conn, table) or not column_exists(conn, table, "user"):
                        continue
                    moved = conn.execute(
                        f'UPDATE {table} SET "user" = %s WHERE "user" = %s', (tiger_id, FIRST_USER)
                    ).rowcount
                    # SET DEFAULT 不接受绑定参数；tiger_id 已过 _safe_id 白名单。
                    conn.execute(f"ALTER TABLE {table} ALTER COLUMN \"user\" SET DEFAULT '{tiger_id}'")
                    if moved:
                        print(f"[收编] {table}: {moved} 行 '{FIRST_USER}' -> {tiger_id}")
            print(f"[收编] 各表 user 列 DEFAULT -> {tiger_id}")
        else:
            print("[跳过] 已按规范 ID 收编过")
        conn.commit()

    if args.users_db:
        with psycopg.connect(args.users_db) as users:
            if not _safe_id(tiger_id):
                raise SystemExit(f"--tiger-id 含非法字符：{tiger_id!r}")
            users.execute(
                "CREATE TABLE IF NOT EXISTS athena_users ("
                "  id TEXT PRIMARY KEY,"
                "  name TEXT NOT NULL,"
                "  created_at TEXT NOT NULL"
                ")"
            )
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            users.execute(
                "INSERT INTO athena_users (id, name, created_at) VALUES (%s, %s, %s)"
                " ON CONFLICT (id) DO UPDATE SET name = excluded.name",
                (tiger_id, FIRST_USER, now),
            )
            users.commit()
            print(f"[目录] athena_users 登记 ({tiger_id}, {FIRST_USER})")
    print("完成。")
    return 0


def _safe_id(value: str) -> bool:
    import re

    return re.fullmatch(r"[A-Za-z0-9_]{1,64}", value) is not None


if __name__ == "__main__":
    raise SystemExit(main())
