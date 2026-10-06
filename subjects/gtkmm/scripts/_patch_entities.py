#!/usr/bin/env python3
"""接线：sync 的实体展开带上 DocBook 自定义实体。"""
from pathlib import Path

p = Path("scripts/sync_upstream.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
    """    direct_children,
    docbook_entities,
    element_text,""",
    """    direct_children,
    docbook_entities,
    element_text,""")

text = text.replace(
    """    load_structure,
    strip_tags,
)""",
    """    load_structure,
    strip_tags,
)

_CUSTOM = docbook_entities()


def expand_md(raw: str) -> str:
    # 标准实体 + DocBook 自定义实体（gtkmm、cpp 等）一起展开
    return expand_entities(raw, _CUSTOM)""",
    1,
)

n1 = text.count("inline_md(expand_entities(text)).strip()")
text = text.replace("inline_md(expand_entities(text)).strip()", "inline_md(expand_md(text)).strip()")
n2 = text.count("inline_md(expand_entities(raw)).strip()")
text = text.replace("inline_md(expand_entities(raw)).strip()", "inline_md(expand_md(raw)).strip()")
n3 = text.count("figure_ref(expand_entities(fig_text))")
text = text.replace("figure_ref(expand_entities(fig_text))", "figure_ref(expand_md(fig_text))")

if "docbook_entities," not in text:
    text = text.replace(
        "    direct_children,\n    element_text,",
        "    direct_children,\n    docbook_entities,\n    element_text,",
    )

p.write_text(text, encoding="utf-8")
print(f"替换：para {n1}、listitem {n2}、figure {n3}；docbook_entities 导入: {'docbook_entities,' in text}")
