#!/usr/bin/env python3
"""题库猜题捷径体检：答案位置是否扎堆、正确项是否总是最长（只报告，不阻断）。

AI 起草的选择题常见两个毛病：答案几乎都放在第 2 个位置，正确项又是最长的那个，
读者不看题干也能蒙对。本脚本扫各应用 content/ 下带 choices 与 answer 的题目，
按应用汇总。判分要求另有出处与考试规范的应用（题源是真实试卷）看数据即可，
不要机械重排。

    python3 scripts/question_bias.py            # 全部应用
    python3 scripts/question_bias.py snake      # 名字包含 snake 的应用
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"node_modules", "archive", "build", "dist", "target", ".cache"}


def questions(node):
    """递归找出所有 {choices 或 options: [str...], answer: int} 形式的题（answer 是选项序号）。"""
    if isinstance(node, dict):
        choices, answer = node.get("choices") or node.get("options"), node.get("answer")
        if isinstance(choices, list) and len(choices) >= 2 and all(isinstance(c, str) for c in choices) and isinstance(answer, int):
            yield node
        for value in node.values():
            yield from questions(value)
    elif isinstance(node, list):
        for item in node:
            yield from questions(item)


def main(argv: list[str]) -> int:
    needle = argv[0] if argv else ""
    rows = []
    for content in sorted(ROOT.glob("*/*/content")) + sorted(ROOT.glob("*/*/src/content")):
        app = content.parent
        if needle not in app.name or SKIP_PARTS & set(app.parts):
            continue
        positions: Counter[int] = Counter()
        longest = total = 0
        for path in content.rglob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for q in questions(data):
                if not 0 <= q["answer"] < len((q.get("choices") or q["options"])):
                    continue
                positions[q["answer"]] += 1
                lengths = [len(c) for c in (q.get("choices") or q["options"])]
                longest += all(lengths[q["answer"]] > n for i, n in enumerate(lengths) if i != q["answer"])  # 并列最长没有信号，不算
                total += 1
        if total:
            rows.append((app.relative_to(ROOT).as_posix(), total, positions, longest))
    print(f"{'应用':<42}{'题数':>6}  答案位置占比（第1/2/3/4…）  正确项独占最长")
    for name, total, positions, longest in sorted(rows, key=lambda r: -max(r[2].values()) / r[1]):
        share = " ".join(f"{positions[i] / total:>4.0%}" for i in range(max(positions) + 1))
        flag = "  ← 位置扎堆" if max(positions.values()) / total > 0.4 and total >= 10 else ""
        flag += "  ← 最长项偏多" if longest / total > 0.5 and total >= 10 else ""
        print(f"{name:<42}{total:>6}  {share:<26}{longest / total:>8.0%}{flag}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    raise SystemExit(main(sys.argv[1:]))
