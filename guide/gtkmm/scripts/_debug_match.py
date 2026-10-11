#!/usr/bin/env python3
"""诊断：为什么塞语 po 与我们快照的 plain 匹配率低。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_po import parse_po, po_to_plain, snapshot_plain  # noqa: E402

SR = Path("C:/Users/tiger/Downloads/gtkmm-documentation.tutorial-doc.master.sr.po")

sr_entries = parse_po(SR.read_text(encoding="utf-8"))
# 找含该句的 sr msgid
needle = "is a new version of the"
sr_hit = None
for mid in sr_entries:
    raw = mid
    if needle in raw:
        sr_hit = mid
        break
print("sr msgid 原文片段:", repr(sr_hit[:120]) if sr_hit else "未找到")
if sr_hit:
    from apply_po import expand_entities
    print("po_to_plain:", repr(po_to_plain(sr_hit)[:120]))

# 我们快照同段的 plain
import re
CHAPTERS = Path(__file__).resolve().parent.parent / "content" / "chapters"
d = None
for f in sorted(CHAPTERS.rglob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for b in data["blocks"]:
        if "is a new version of the" in b.get("text", ""):
            print("快照所在:", data["section"])
            print("快照 plain:", repr(snapshot_plain(b["text"])[:120]))
            d = (f, data, b)
            break
    if d:
        break
EOF_MARKER_NOT_NEEDED = None
