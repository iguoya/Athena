#!/usr/bin/env python3
"""apply_po 扩展：--fix 模式——按官方 po 修正错位/漂移的译文（内容寻址）。"""
from pathlib import Path

p = Path("scripts/apply_po.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
    '''def main() -> int:
    force_utf8()
    apply = "--apply" in sys.argv
    po_entries = parse_po(PO_PATH.read_text(encoding="utf-8"))
    # 纯文本 → 译文（po 的 msgstr 同样转纯文本；多个 msgid 归一后撞键时先到先得）
    plain_zh = {}
    for msgid, msgstr in po_entries.items():
        if not msgstr.strip():
            continue
        key = po_to_plain(msgid)
        plain_zh.setdefault(key, po_to_plain(msgstr))

    filled = skipped_existing = not_found = 0''',
    '''def main() -> int:
    force_utf8()
    apply = "--apply" in sys.argv
    fix = "--fix" in sys.argv
    po_entries = parse_po(PO_PATH.read_text(encoding="utf-8"))
    # 纯文本 → 译文（po 的 msgstr 同样转纯文本；多个 msgid 归一后撞键时先到先得）
    plain_zh = {}
    zh_to_own: dict[str, str] = {}
    for msgid, msgstr in po_entries.items():
        if not msgstr.strip():
            continue
        key = po_to_plain(msgid)
        zh_plain = po_to_plain(msgstr)
        plain_zh.setdefault(key, zh_plain)
        zh_to_own.setdefault(zh_plain, key)

    misplaced = 0''')

text = text.replace(
    '''        for block in data.get("blocks", []):
            if block["type"] not in ("para", "listitem") or block.get("zh"):
                continue
            key = snapshot_plain(block["text"])
            zh = plain_zh.get(key)
            if zh:
                block["zh"] = zh
                block.pop("status", None)
                block.pop("stale_from", None)
                filled += 1
                changed = True
            else:
                not_found += 1''',
    '''        for block in data.get("blocks", []):
            if block["type"] not in ("para", "listitem"):
                continue
            own = snapshot_plain(block["text"])
            if block.get("zh"):
                if not fix:
                    continue
                # 错位修复：zh 恰是官方 po 里另一段的译文 → 内容寻址重挂
                zh_plain = snapshot_plain(block["zh"])
                owner = zh_to_own.get(zh_plain)
                if owner is not None and owner != own:
                    correct = plain_zh.get(own)
                    if correct:
                        block["zh"] = correct
                    else:
                        block["zh"] = None
                        block["status"] = "untranslated"
                    block.pop("stale_from", None)
                    misplaced += 1
                    changed = True
                continue
            key = own
            zh = plain_zh.get(key)
            if zh:
                block["zh"] = zh
                block.pop("status", None)
                block.pop("stale_from", None)
                filled += 1
                changed = True
            else:
                not_found += 1''')

text = text.replace(
    '''    verb = "已填充" if apply else "可填充（--apply 生效）"
    print(f"官方 po 对齐：{verb} {filled} 段；po 中无对应译文 {not_found} 段（留给自译流程）")
    return 0''',
    '''    verb = "已填充" if apply else "可填充（--apply 生效）"
    print(f"官方 po 对齐：{verb} {filled} 段；po 中无对应译文 {not_found} 段（留给自译流程）")
    fixed_verb = "已修正" if apply else "可修正（--fix 生效）"
    print(f"错位审计：{fixed_verb} {misplaced} 段（zh 恰为 po 中另一段的译文）")
    return 0''')

p.write_text(text, encoding="utf-8")
print("apply_po.py --fix 完成")
