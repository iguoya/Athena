#!/usr/bin/env python3
"""把进度库 dump 成 SQL 文本，给 git diff 当 textconv 用（ADR 0053）。

进度库以 SQLite 二进制形式随仓库走，默认 diff 只会说一句
"Binary files differ"。挂上这个之后 `git diff` 和 `git log -p` 能看见到底哪
条作答记录变了——需要在冲突里二选一时，这是唯一的判断依据。

用 Python 自带的 sqlite3 模块而不是 sqlite3 命令行：三个平台都有 Python，
但 Windows 上默认没有 sqlite3.exe（ADR 0047）。

git 那边由 `launcher sync` 配好，等价于：

    git config diff.sqlite.textconv "python3 scripts/db-textconv.py"
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"用法：{Path(sys.argv[0]).name} <learning.db>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    # git 会把空树或缺失的一边喂成空文件，照二进制读出来是 0 字节。
    if not path.is_file() or path.stat().st_size == 0:
        return 0

    # 只读打开，绝不让 diff 这种旁路动到真库（默认连接会顺手建文件、跑恢复）。
    uri = f"file:{path.as_posix()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            for line in connection.iterdump():
                print(line)
    except sqlite3.DatabaseError as error:
        # 不是库、或者库损坏时，如实说一句就好：textconv 失败会让 git 整个
        # diff 报错，而我们只是想看内容。
        print(f"-- 无法读取 {path.name}：{error}", file=sys.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
