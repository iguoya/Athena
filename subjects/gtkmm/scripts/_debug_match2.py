#!/usr/bin/env python3
"""对比未命中段的两侧 plain 全文，找第一个差异。"""
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_po import parse_po, po_to_plain, snapshot_plain  # noqa: E402

sr_entries = parse_po(Path("C:/Users/tiger/Downloads/gtkmm-documentation.tutorial-doc.master.sr.po").read_text(encoding="utf-8"))
sr_plain = {po_to_plain(m) for m in sr_entries.values() if m.strip()}

CHAPTERS = Path("content/chapters")
target = None
for f in sorted(CHAPTERS.rglob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for b in data["blocks"]:
        if b["type"] in ("para", "listitem") and "is a new version of the" in b.get("text", ""):
            target = (data["section"], b)
            break
    if target:
        break

section, block = target
ours = snapshot_plain(block["text"])
# 在 sr_plain 里找最接近的
best = max(sr_plain, key=lambda s: difflib.SequenceMatcher(None, ours, s).ratio())
ratio = difflib.SequenceMatcher(None, ours, best).ratio()
print(f"快照节: {section} / 段 sha: {block['sha'][:12]}")
print(f"我们的 plain ({len(ours)} 字): {ours[:150]}")
print(f"sr 最接近    ({len(best)} 字): {best[:150]}")
print(f"相似度: {ratio:.2%}")
# 找第一个差异字符
sm = difflib.SequenceMatcher(None, ours, best)
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != "equal":
        print(f"差异 {op}: ours[{i1}:{i2}]={ours[i1:i2]!r}  best[{j1}:{j2}]={best[j1:j2]!r}")
        break
