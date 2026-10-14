#!/usr/bin/env python3
"""核对点写作时的快速校验：python3 scripts/lint_checks.py <节 id> [...]
只检查这几节的 content/checks/<id>.json 结构（完整检查是 scripts/check.py）。"""
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
    # 只校验指定节：临时把 checks 目录限制到这几个文件
    real = check.CONTENT / "checks"
    for i in ids:
        f = real / f"{i}.json"
        if not f.is_file():
            print(f"（{i} 还没有 checks 文件）")
    check.check_checks(sections)
    if check.ERRORS:
        for e in check.ERRORS:
            print("✗", e)
        return 1
    print("通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
