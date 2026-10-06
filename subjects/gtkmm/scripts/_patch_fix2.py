#!/usr/bin/env python3
"""精准修补 apply_po.main 的变量初始化。"""
from pathlib import Path

p = Path("scripts/apply_po.py")
text = p.read_text(encoding="utf-8")

old = '''def main() -> int:
    force_utf8()
    apply = "--apply" in sys.argv
    po_entries = parse_po(PO.read_text(encoding="utf-8"))
    # 纯文本 → 译文（po 的 msgstr 同样转纯文本；多个 msgid 归一后撞键时先到先得）
    plain_zh: dict[str, str] = {}
    for msgid, msgstr in po_entries.items():
        if not msgstr.strip():
            continue
        key = po_to_plain(msgid)
        plain_zh.setdefault(key, po_to_plain(msgstr))

    filled = skipped_existing = not_found = 0'''
new = '''def main() -> int:
    force_utf8()
    apply = "--apply" in sys.argv
    fix = "--fix" in sys.argv
    po_entries = parse_po(PO.read_text(encoding="utf-8"))
    # 纯文本 → 译文（po 的 msgstr 同样转纯文本；多个 msgid 归一后撞键时先到先得）
    plain_zh: dict[str, str] = {}
    zh_to_own: dict[str, str] = {}
    for msgid, msgstr in po_entries.items():
        if not msgstr.strip():
            continue
        key = po_to_plain(msgid)
        zh_plain = po_to_plain(msgstr)
        plain_zh.setdefault(key, zh_plain)
        zh_to_own.setdefault(zh_plain, key)

    filled = skipped_existing = not_found = misplaced = 0'''
assert old in text, "main 头部未匹配"
text = text.replace(old, new)
p.write_text(text, encoding="utf-8")
print("初始化修补完成")
