#!/usr/bin/env python3
"""把旧的 SQLite 进度库一次性导入中心 PostgreSQL（ADR 0067）。

    python3 scripts/migrate_progress_to_pg.py --dry-run     # 只看会导入多少条
    python3 scripts/migrate_progress_to_pg.py               # 真导入

连接配置和客户端读同一个地方，**脚本不收密码参数**（命令行会进 shell 历史）：
环境变量 `ATHENA_DRIVER_DB`（完整 URI），或用户数据目录的 `db.json`
（macOS `~/Library/Application Support/AthenaDriver`、Windows `%APPDATA%\\AthenaDriver`、
Linux `$XDG_DATA_HOME` 或 `~/.local/share` 下的 `AthenaDriver`）。

安全规矩：
- **目标表非空就拒绝**（避免重复导入）；确要合并，先自己清空目标表。
- 全部在一个事务里：中途出错整体回滚，库不会留下导了一半的数据。
- 导完逐表核对条数，对不上就回滚。
- 只读源库，不改它。导入成功之前不要删 `progress/learning.db`。

建表直接取自 `lib/progress.dart` 的 `_ensureSchema`（同一份语句，不在这里再抄一遍），
这样客户端和迁移脚本不会各自漂移。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

APP_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = APP_ROOT / "progress" / "learning.db"
PROGRESS_DART = APP_ROOT / "lib" / "progress.dart"

# 表名 -> 要导入的列（不含 id：PG 里 id 是 GENERATED ALWAYS，由库自增；
# id 只用作拉取游标，不需要保留旧值，按旧 id 顺序插入即可保持先后）。
TABLES: dict[str, list[str]] = {
    "attempts": ["question_id", "topic_id", "subject_id", "correct", "duration_ms", "hesitant", "at"],
    "exams": ["subject_id", "score", "passed", "at"],
    "notices": ["kind", "title", "body", "at", "read"],
    "drill_runs": ["item_id", "mistakes", "at"],
    "point_notes": ["item_id", "step", "text", "at"],
    "point_photos": ["item_id", "step", "file", "caption", "at", "removed"],
    "rehearsals": ["item_id", "missed", "total", "at"],
    "drill_notes": ["item_id", "text", "at"],
    # 主键是业务键的表，没有 id 列。
    "achievements": ["key", "at"],
    "exam_drafts": [
        "draft_key", "subject_id", "title", "question_ids", "question_count", "minutes", "pass_score",
        "points_per_question", "mix", "full_bank", "picked", "started_at", "saved_at",
    ],
}
HAS_ID = {name for name in TABLES if name not in ("achievements", "exam_drafts")}
# 导入时的先后：先有业务键的小表，再大表；没有外键，顺序只是为了输出好读。


def user_data_dir() -> Path:
    """与 lib/progress.dart 的 userDataDir() 保持一致。"""
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA") or os.environ["USERPROFILE"])
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return root / "AthenaDriver"


def load_config() -> dict:
    uri = os.environ.get("ATHENA_DRIVER_DB")
    if uri:
        parts = urlsplit(uri)
        return {
            "host": parts.hostname, "port": parts.port or 5432, "database": parts.path.lstrip("/"),
            "username": unquote(parts.username or ""), "password": unquote(parts.password or ""),
        }
    path = user_data_dir() / "db.json"
    if not path.is_file():
        sys.exit(
            f"没找到数据库连接配置。设环境变量 ATHENA_DRIVER_DB（postgresql://用户:密码@主机:5432/库），"
            f"或先打开驾考应用，在配置对话框里填好（会写到 {path}）。"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def schema_statements() -> list[str]:
    """取客户端 `_ensureSchema` 里的建表语句，保证与应用一致。"""
    source = PROGRESS_DART.read_text(encoding="utf-8")
    statements = re.findall(r"CREATE TABLE IF NOT EXISTS \w+ \(.*?\n\s*\)", source, flags=re.S)
    if len(statements) != len(TABLES):
        sys.exit(f"在 {PROGRESS_DART.name} 里找到 {len(statements)} 条建表语句，预期 {len(TABLES)}——表结构变了，先更新本脚本。")
    return statements


def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows 控制台默认不是 UTF-8（ADR 0047）
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="旧 SQLite 进度库（默认 progress/learning.db）")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写入")
    args = parser.parse_args()

    if not args.source.is_file():
        sys.exit(f"源库不存在：{args.source}")

    try:
        import psycopg
    except ImportError:
        sys.exit('缺少 psycopg：pip install "psycopg[binary]"')

    # 以只读方式打开源库，保证不会动到它。
    source = sqlite3.connect(f"file:{args.source.resolve().as_posix()}?mode=ro", uri=True)
    counts = {name: source.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in TABLES}
    print("源库（SQLite）：" + "，".join(f"{name} {n}" for name, n in counts.items() if n) or "（空）")
    if args.dry_run:
        print("--dry-run：未写入任何数据。")
        return 0

    cfg = load_config()
    with psycopg.connect(
        host=cfg["host"], port=cfg["port"], dbname=cfg["database"], user=cfg["username"],
        password=cfg["password"], connect_timeout=5,
    ) as conn:
        with conn.transaction():
            for statement in schema_statements():
                conn.execute(statement)

            occupied = {
                name: n for name in TABLES if (n := conn.execute(f"SELECT count(*) FROM {name}").fetchone()[0])
            }
            if occupied:
                sys.exit(
                    "目标库不是空的，为避免重复导入已停止（未做任何改动）："
                    + "，".join(f"{k} {v}" for k, v in occupied.items())
                )

            for name, columns in TABLES.items():
                order = " ORDER BY id" if name in HAS_ID else ""
                rows = source.execute(f"SELECT {', '.join(columns)} FROM {name}{order}").fetchall()
                if not rows:
                    continue
                column_list = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                with conn.cursor() as cursor:
                    cursor.executemany(f"INSERT INTO {name} ({column_list}) VALUES ({placeholders})", rows)

            # 逐表核对；对不上就抛出，事务整体回滚。
            mismatched = []
            for name, expected in counts.items():
                actual = conn.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                if actual != expected:
                    mismatched.append(f"{name}: 源 {expected} / 目标 {actual}")
            if mismatched:
                raise RuntimeError("条数核对失败，已回滚：" + "；".join(mismatched))

    print("已导入并核对一致：" + "，".join(f"{name} {n}" for name, n in counts.items() if n))
    print("确认应用能正常读到数据后，再把 progress/learning.db 退出版本库。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
