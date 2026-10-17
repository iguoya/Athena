#!/usr/bin/env python3
"""翻译术语约定的检查与批量统一（应用 ADR 0010，规则在 content/glossary.json）。

    python scripts/glossary.py            # 检查：禁用写法出现在哪里（有就退出码 1）
    python scripts/glossary.py --apply    # 按 replace 规则批量改写，打印每个文件的改动数

作用范围：章节快照的 zh（唯一手写译文）、curriculum.json、demos.json、vocab.json、
src/simulations.tsx。po-units/ 是社区 PO 的镜像、ADR 是只增不改的记录，都不在其内。
JSON 文件只在字符串值上替换（按文件原文做字符串替换，不重排版面，换行风格保持原样）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"


def rules() -> list[dict]:
    return json.loads((CONTENT / "glossary.json").read_text(encoding="utf-8"))["rules"]


def targets() -> list[Path]:
    files = sorted((CONTENT / "chapters").glob("*/*.json"))
    files += [CONTENT / "curriculum.json", CONTENT / "demos.json", CONTENT / "vocab.json",
              ROOT / "src" / "simulations.tsx"]
    return files


def scan_text(path: Path) -> list[str]:
    """返回需要检查的文本片段：章节快照只看 zh，其余整文件。"""
    raw = path.read_text(encoding="utf-8")
    if path.parent.parent.name == "chapters":
        data = json.loads(raw)
        return [b.get("zh") or "" for b in data.get("blocks", [])]
    return [raw]


def violations() -> list[str]:
    out = []
    for path in targets():
        for piece in scan_text(path):
            for rule in rules():
                for pattern in rule["avoid"]:
                    for m in re.finditer(pattern, piece):
                        around = piece[max(0, m.start() - 10): m.end() + 10].replace("\n", " ")
                        out.append(f"{path.relative_to(ROOT)}: 「{m.group(0)}」应为「{rule['use']}」…{around}…")
    return out


def apply() -> int:
    total = 0
    for path in targets():
        raw = path.read_bytes().decode("utf-8")
        new = raw
        if path.parent.parent.name == "chapters":
            # 只改 "zh" 字符串值：逐个 zh 值做替换，英文原文不动
            data = json.loads(raw)
            for block in data.get("blocks", []):
                zh = block.get("zh")
                if not zh:
                    continue
                fixed = zh
                for rule in rules():
                    for pattern, repl in rule["replace"]:
                        fixed = re.sub(pattern, repl, fixed)
                if fixed != zh:
                    old_json, new_json = json.dumps(zh, ensure_ascii=False), json.dumps(fixed, ensure_ascii=False)
                    assert new.count(old_json) >= 1, (path, zh[:20])
                    new = new.replace(old_json, new_json, 1) if new.count(old_json) == 1 else new.replace(old_json, new_json)
        else:
            for rule in rules():
                for pattern, repl in rule["replace"]:
                    new = re.sub(pattern, repl, new)
        if new != raw:
            path.write_bytes(new.encode("utf-8"))
            changed = sum(1 for a, b in zip(raw.splitlines(), new.splitlines()) if a != b)
            total += changed
            print(f"  {path.relative_to(ROOT)}: {changed} 行")
    return total


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    if "--apply" in sys.argv:
        print(f"共改 {apply()} 行")
        return 0
    found = violations()
    for line in found:
        print("  ✗", line)
    print(f"术语约定检查：{len(found)} 处违例" if found else "术语约定检查通过")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
