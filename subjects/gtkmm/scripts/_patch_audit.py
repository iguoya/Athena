#!/usr/bin/env python3
"""一次性补丁：check.py 增加译文错位审计（内容寻址，防顺序漂移复发）。"""
from pathlib import Path

p = Path("scripts/check.py")
text = p.read_text(encoding="utf-8")

# 1) 导入 apply_po 的解析函数
text = text.replace(
    "from extract_source import DOCBOOK, load_structure  # noqa: E402",
    """from apply_po import parse_po, po_to_plain, snapshot_plain  # noqa: E402
from extract_source import DOCBOOK, load_structure  # noqa: E402

PO_PATH = (PROJECT_ROOT / "upstream" / "gtkmm-documentation" / "docs"
           / "tutorial" / "zh_CN" / "zh_CN.po")""",
)

# 2) 错位审计函数 + 接入 main（在 check_manifest 之后）
old_main = '''    course = load_json(CONTENT_DIR / "curriculum.json")
    kp_ids, course_refs, lab_refs = check_curriculum(course or {}, official)
    manifest = load_json(CONTENT_DIR / "demos.json")
    check_manifest(manifest or {}, kp_ids, course_refs, lab_refs)'''
new_main = '''    course = load_json(CONTENT_DIR / "curriculum.json")
    kp_ids, course_refs, lab_refs = check_curriculum(course or {}, official)
    manifest = load_json(CONTENT_DIR / "demos.json")
    check_manifest(manifest or {}, kp_ids, course_refs, lab_refs)
    check_alignment()'''
assert old_main in text
text = text.replace(old_main, new_main)

# 3) 审计函数本体（插在 main 之前）
audit_fn = '''def check_alignment() -> None:
    """译文错位审计（内容寻址）：官方 po 中每条译文唯一对应一段原文。

    若某段的 zh 恰好等于 po 里「另一段」的译文，说明发生了顺序漂移——
    这是早期按顺序迁移译文的遗留事故，此处永久守门（应用 ADR 0002）。
    """
    if not PO_PATH.is_file():
        return
    entries = parse_po(PO_PATH.read_text(encoding="utf-8"))
    plain_zh = {}
    for msgid, msgstr in entries.items():
        if msgstr.strip():
            plain_zh.setdefault(po_to_plain(msgid), po_to_plain(msgstr))
    zh_to_own = {}
    for own, zh in plain_zh.items():
        zh_to_own.setdefault(zh, own)

    for path in sorted(CONTENT_DIR.rglob("chapters/*/*.json")):
        data = load_json(path)
        if not data:
            continue
        section = data.get("section", path.stem)
        for block in data.get("blocks", []):
            if block["type"] not in ("para", "listitem") or not block.get("zh"):
                continue
            own = snapshot_plain(block["text"])
            zh_plain = snapshot_plain(block["zh"])
            owner = zh_to_own.get(zh_plain)
            if owner is not None and owner != own:
                fail(
                    f"chapters/{section}: 段落译文错位（该译文对应官方 po 的另一段）"
                    f"——先跑 scripts/apply_po.py --fix 修正：{own[:50]!r}"
                )


'''
anchor = "def main() -> int:"
assert anchor in text
text = text.replace(anchor, audit_fn + anchor, 1)

p.write_text(text, encoding="utf-8")
print("check.py 错位审计已接入")
