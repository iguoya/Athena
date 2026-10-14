#!/usr/bin/env python3
"""用真 SymPy 复跑教程里的每个 `>>>` 示例，把输出与教程印的输出对照（ADR 0163 决策 4）。

    <有 sympy 的 python> scripts/verify_examples.py [页 id …]

doctest 按页顺序执行（后面的块依赖前面的变量，与读者的操作一致）。教程原文里标了 `# doctest: +SKIP` 的跳过。
对不上的逐条打印，退出码 1；这样上游或本机 SymPy 版本一变，马上看得出哪个示例不再成立，而不是悄悄漂移。
"""
from __future__ import annotations

import doctest
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))


def page_source(pid: str) -> str:
    """把快照里的代码块按原顺序拼回一份 doctest 文本（块之间空一行）。"""
    data = json.loads((ROOT / "content" / "sections" / f"{pid}.json").read_text(encoding="utf-8"))
    out: list[str] = []

    def walk(bl):
        for b in bl:
            if b["k"] == "code":
                out.append(b["text"])
            if "blocks" in b:
                walk(b["blocks"])
            if b["k"] == "list":
                for it in b["items"]:
                    walk(it)

    walk(data["blocks"])
    return "\n\n".join(out) + "\n"


# 教程里仍是 Python 2 年代的浮点输出（位数少），现在的 Python 打印完整的 repr。数值是对的、只是位数不同：
# 登记在这里并说明，而不是悄悄放宽比较。键是 (页, 示例源码)。
KNOWN_STALE = {
    ("basic_operations", "f(0.1)"): "教程印 0.0998334166468（Python 2 的 12 位），现在是 0.09983341664682815",
    ("intro", "math.sqrt(8)"): "教程印 2.82842712475（Python 2 的 12 位），现在是 2.8284271247461903",
}


class Runner(doctest.DocTestRunner):
    known = 0

    def report_failure(self, out, test, example, got):
        if (test.name, example.source.strip()) in KNOWN_STALE:
            self.known += 1
            return
        super().report_failure(out, test, example, got)


def main() -> int:
    import sympy

    pages = sys.argv[1:] or [p.stem for p in sorted((ROOT / "content" / "sections").glob("*.json"))]
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS | doctest.IGNORE_EXCEPTION_DETAIL
    bad = total = 0
    for pid in pages:
        text = page_source(pid)
        parser = doctest.DocTestParser()
        globs: dict = {}
        test = parser.get_doctest(text, globs, pid, None, 0)
        runner = Runner(optionflags=flags, verbose=False)
        runner.run(test, out=sys.__stdout__.write)
        total += len(test.examples)
        bad += runner.failures - runner.known
        extra = f"，另有 {runner.known} 个是已登记的旧输出" if runner.known else ""
        print(f"{pid}: {len(test.examples)} 个示例，{runner.failures - runner.known} 个对不上{extra}")
    print(f"共 {total} 个示例，{bad} 个对不上（SymPy {sympy.__version__}）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
