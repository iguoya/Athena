"""受限 markdown 序列化：DocBook 行内标签 → 粗体/斜体/行内代码/链接。

不变量：strip_inline_md(inline_md(x)) == strip_tags(x)——序列化只改展示层，
段落指纹按纯文本计算不受影响（应用 ADR 0002 的格式保真约定）。
"""
from __future__ import annotations

import re

_MD_CODE_TAGS = {
    "code", "command", "filename", "literal", "classname",
    "typename", "constant", "function", "replaceable",
    "parameter", "application", "systemitem", "guilabel",
    "guimenuitem", "option", "varname", "structname", "type",
}

_ENTITIES = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "&apos;": "'", "&nbsp;": " ",
}


def expand_entities(text: str, custom: dict[str, str] | None = None) -> str:
    """只展开实体（含值内含标签的 DocBook 自定义实体），保留其余标签。"""
    for name, value in sorted((custom or {}).items(), key=lambda kv: -len(kv[0])):
        text = text.replace(f"&{name};", value)
    for entity, char in _ENTITIES.items():
        text = text.replace(entity, char)
    return text


def _innermost(tag: str, source: str):
    """找最内层的 <tag>...</tag> 片段（内部不含同名标签）。"""
    pattern = re.compile(
        "<" + tag + r"(\s[^>]*)?>((?:(?!<" + tag + r"[\s>]|</" + tag + r">).)*)</" + tag + ">",
        re.S,
    )
    return pattern.search(source)


def inline_md(source: str) -> str:
    result = source
    for _ in range(50):  # 收敛保护
        changed = False
        for tag in sorted(_MD_CODE_TAGS, key=len, reverse=True):
            while True:
                m = _innermost(tag, result)
                if not m:
                    break
                inner = inline_md(m.group(2))
                result = result[: m.start()] + "`" + inner + "`" + result[m.end():]
                changed = True
        em = re.compile(
            r"<emphasis([^>]*)>((?:(?!<emphasis[\s>]|</emphasis>).)*)</emphasis>", re.S
        ).search(result)
        if em:
            role = re.search(r'role="(\w+)"', em.group(1))
            inner = inline_md(em.group(2))
            mark = "**" if role and role.group(1) == "bold" else "*"
            result = result[: em.start()] + mark + inner + mark + result[em.end():]
            changed = True
        link = re.compile(
            r"<(link|ulink)([^>]*)>((?:(?!<\1[\s>]|</\1>).)*)</\1>", re.S
        ).search(result)
        if link:
            href = re.search(r'xlink:href="([^"]+)"|href="([^"]+)"', link.group(2))
            url = (href.group(1) or href.group(2)) if href else ""
            inner = inline_md(link.group(3))
            result = result[: link.start()] + "[" + inner + "](" + url + ")" + result[link.end():]
            changed = True
        if not changed:
            break
    # quote 与其余未知标签剥壳保文本（不改变指纹）
    result = re.sub(
        r"</?(?:quote|citetitle|accel|keycap|keycombo|mousebutton|html:[a-z]+)(?:\s[^>]*)?>",
        "", result,
    )
    result = re.sub(r"<[^>]+>", "", result)
    return result


def strip_inline_md(text: str) -> str:
    """把受限 markdown 还原成纯文本（指纹计算的规范化输入）。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    return text
