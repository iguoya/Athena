#!/usr/bin/env python3
"""译文的导出与导入（让翻译不必直接改快照 JSON）。

  python3 scripts/tr.py export <节 id> [--all]      输出待译单元（zh 为空；--all 含已译）：[{"sha","en"}...]
  python3 scripts/tr.py import <节 id> <文件>        读入译文并写回快照与课表进度；文件是 .json（{"<sha>": "译文"}）
                                                    或 .txt（每条 `@@ <sha>` 一行、下面是译文；公式里的反斜杠不用转义）
  python3 scripts/tr.py title <节 id> "中文标题"      （极少用）改节的中文标题；平时标题在 scope.json

导入时逐条校验：sha 必须存在；译文里的 $…$ 公式集合必须与原文一致；不能是空串。
有问题的条目整条拒绝并列出原因，其余照常写入。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import code_spans, inline_math, units  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEC = ROOT / "content" / "sections"


def all_units(data: dict):
    yield from units(data["blocks"])


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd, sid = sys.argv[1], sys.argv[2]
    path = SEC / f"{sid}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if cmd == "export":
        want_all = "--all" in sys.argv
        out, seen = [], set()
        for u in all_units(data):
            if (want_all or not u["zh"]) and u["sha"] not in seen:
                seen.add(u["sha"])
                out.append({"sha": u["sha"], "en": u["en"]})
        json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return 0
    if cmd == "import":
        src = Path(sys.argv[3])
        if src.suffix == ".txt":
            tr, cur = {}, None
            for line in src.read_text(encoding="utf-8").splitlines():
                if line.startswith("@@ "):
                    cur = line[3:].strip()
                    tr[cur] = ""
                elif cur is not None:
                    tr[cur] += (" " if tr[cur] else "") + line.strip()
        else:
            tr = json.loads(src.read_text(encoding="utf-8"))
        by_sha: dict[str, list[dict]] = {}
        for u in all_units(data):
            by_sha.setdefault(u["sha"], []).append(u)
        ok = bad = 0
        for sha, zh in tr.items():
            if sha not in by_sha:
                print(f"✗ {sha}: 本节没有这个单元")
                bad += 1
                continue
            en = by_sha[sha][0]["en"]
            if not isinstance(zh, str) or not zh.strip():
                print(f"✗ {sha}: 译文为空")
                bad += 1
                continue
            if sorted(inline_math(zh)) != sorted(inline_math(en)):
                print(f"✗ {sha}: 公式与原文不一致\n    en: {en[:100]}\n    zh: {zh[:100]}")
                bad += 1
                continue
            if code_spans(zh) != code_spans(en):
                print(f"✗ {sha}: 行内代码（反引号里的）与原文不一致，代码不翻译\n    en: {en[:100]}\n    zh: {zh[:100]}")
                bad += 1
                continue
            for u in by_sha[sha]:  # 同一指纹的重复单元一并写入
                u["zh"] = zh.strip()
            ok += 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        left = sum(1 for u in all_units(data) if not u["zh"])
        print(f"写入 {ok} 条，拒绝 {bad} 条；本节还剩 {left} 个单元未译")
        # 课表里的进度数字由 sync_upstream.py 统一刷新（并行翻译时不在这里写 curriculum.json，避免互相覆盖）
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
