#!/usr/bin/env python3
"""分析塞尔维亚语 po：覆盖力、维护方式、对我们的借鉴。"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_po import parse_po, po_to_plain, snapshot_plain  # noqa: E402

SRC = Path("C:/Users/tiger/Downloads/gtkmm-documentation.tutorial-doc.master.sr.po")
CHAPTERS = Path(__file__).resolve().parent.parent / "content" / "chapters"

po_text = SRC.read_text(encoding="utf-8")
for line in po_text.splitlines()[:14]:
    if any(k in line for k in ("Project-Id", "POT-Creation", "PO-Revision", "Last-Trans", "Language-Team", "X-Generator")):
        print(line.strip())

entries = parse_po(po_text)
total = len(entries)
translated = sum(1 for m in entries.values() if m.strip())
print(f"\n条目 {total}，非空译文 {translated}（{translated / total:.0%}）")

# 对我们快照的覆盖：1541 个文字段中，塞语有多少段有译文（证明管线覆盖力）
sr_plain = {po_to_plain(m) for m in entries.values() if m.strip()}
covered = missing = 0
missing_samples = []
for f in sorted(CHAPTERS.rglob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    for b in d["blocks"]:
        if b["type"] in ("para", "listitem"):
            if snapshot_plain(b["text"]) in sr_plain:
                covered += 1
            else:
                missing += 1
                if len(missing_samples) < 5:
                    missing_samples.append(b["text"][:60])
print(f"我们 1541 段中塞语有译文的: {covered}（{covered / (covered + missing):.0%}）；塞语也没翻的: {missing}")
for s in missing_samples:
    print("  塞语也缺:", s)

# 术语风格抽样：widget/signal/container 的塞语译法
samples_terms = ["widget", "signal", "container", "packing"]
print("\n塞语术语抽样：")
for m, zh in list(entries.items())[:0]:
    pass
count = 0
for mid, mstr in entries.items():
    if not mstr.strip():
        continue
    low = mstr.lower()
    for t in samples_terms:
        if t in mid.lower() and count < 6:
            print(f"  {t}: {mstr[:60]}")
            count += 1
            break
