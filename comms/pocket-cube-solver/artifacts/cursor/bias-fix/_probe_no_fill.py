#!/usr/bin/env python3
"""试跑：只用手写选项 + 位置轮转，不加任何填充尾巴。"""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# 动态加载 build_patches 里的静态表与 balance/rotate
spec = importlib.util.spec_from_file_location("bp", HERE / "build_patches.py")
bp = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bp)

spec2 = importlib.util.spec_from_file_location("cp", HERE / "check_patch.py")
cp = importlib.util.module_from_spec(spec2)
assert spec2.loader is not None
spec2.loader.exec_module(cp)

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


def unique_longest(choices, answer) -> bool:
    L = len(choices[answer])
    return all(len(c) < L for i, c in enumerate(choices) if i != answer)


def report(name, rows):
    n = len(rows)
    pos = Counter(r["answer"] for r in rows)
    ul = sum(1 for r in rows if unique_longest(r["choices"], r["answer"]))
    bad_len = []
    for r in rows:
        if not cp.length_ok(r["choices"], r["answer"]):
            bad_len.append(r["id"])
    print(f"\n=== {name} ===")
    print(
        "  pos:",
        " ".join(f"{i}:{pos[i]}({pos[i]/n:.0%})" for i in range(4)),
    )
    print(f"  unique-longest: {ul}/{n} = {ul/n:.0%}")
    print(f"  bad_len (>40%): {len(bad_len)}")
    for qid in bad_len[:12]:
        print(f"    - {qid}")


def main():
    snake = bp.balance(bp.SNAKE, [11, 11, 11, 11], 12)
    chess = bp.balance(bp.CHESS, [5, 5, 6, 5], 6)
    cpp = bp.balance(bp.CPP, [5, 4, 5, 4], 5)
    # 正确项尽量还原原文（含必要改写）
    snake = bp.restore_correct_text(snake, bp.load_originals("snake"))
    chess = bp.restore_correct_text(chess, bp.load_originals("chinese-chess"))
    cpp = bp.restore_correct_text(cpp, bp.load_originals("c-plus-plus"))
    report("snake", snake)
    report("chess", chess)
    report("cpp", cpp)


if __name__ == "__main__":
    main()
