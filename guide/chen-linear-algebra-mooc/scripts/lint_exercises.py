#!/usr/bin/env python3
"""「原书题目」写作时的快速校验：python3 scripts/lint_exercises.py <节 id> [...]
只检查这几章的 content/exercises/<id>.json（含用真 Octave 复算答案；完整检查是 scripts/check.py）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402


def main() -> int:
    ids = sys.argv[1:]
    if not ids:
        print(__doc__)
        return 2
    sections = {}
    for i in ids:
        p = check.CONTENT / "sections" / f"{i}.json"
        if p.is_file():
            sections[i] = json.loads(p.read_text(encoding="utf-8"))
        else:
            check.fail(f"没有这一节：{i}")
    for i in ids:
        if not (check.CONTENT / "exercises" / f"{i}.json").is_file():
            print(f"（{i} 还没有 exercises 文件）")
    check.check_exercises(sections)
    if check.ERRORS:
        for e in check.ERRORS:
            print("✗", e)
        return 1
    print("通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
