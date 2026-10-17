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
    "&apos;": "'", "&nbsp;": " ", "&#160;": "\u00a0",
}


# 实体展开出来的 < 与 > 是正文字符（如 sigc::slot&lt;R(Args...)&gt;），不是标签。
# inline_md 末尾的「剥未知标签」正则分不清二者，所以展开时先换成私有区占位符，
# 序列化完再用 restore_angles 还原；否则模板参数、Pango 标记等会被当标签吞掉。
_LT, _GT = "", ""


def expand_entities(text: str, custom: dict[str, str] | None = None, keep_angle: bool = False) -> str:
    """只展开实体（含值内含标签的 DocBook 自定义实体），保留其余标签。

    keep_angle=True 时 &lt; &gt; 展开成占位符而非 < >，调用方在剥完标签后
    用 restore_angles 还原。
    """
    # 自定义实体的值里还可能引用别的实体（url_refdocs_base_gtk = "&url_refdocs_base_gtk_html;classGtk_1_1"），
    # 一遍替换会漏掉新冒出来的引用，所以替换到不再变化为止
    for _ in range(5):
        before = text
        for name, value in sorted((custom or {}).items(), key=lambda kv: -len(kv[0])):
            text = text.replace(f"&{name};", value)
        if text == before:
            break
    for entity, char in _ENTITIES.items():
        if keep_angle and entity in ("&lt;", "&gt;"):
            char = _LT if entity == "&lt;" else _GT
        text = text.replace(entity, char)
    # 数字字符引用（&#169; &#xA9;）：DocBook 里用来写 © ü ß 等，不展开会把「&#169;」原样留在正文里
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&#[xX]([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
    return text


def restore_angles(text: str) -> str:
    return text.replace(_LT, "<").replace(_GT, ">")


def _innermost(tag: str, source: str):
    """找最内层的 <tag>...</tag> 片段（内部不含同名标签）。"""
    pattern = re.compile(
        "<" + tag + r"(\s[^>]*)?>((?:(?!<" + tag + r"[\s>]|</" + tag + r">).)*)</" + tag + ">",
        re.S,
    )
    return pattern.search(source)


def inline_md(source: str) -> str:
    result = source
    # 自闭合 <link .../>（无子内容）：官网以目标本身作为链接文本渲染，
    # 不展开则剥标签后正文留下空洞
    result = re.sub(
        r'<link\s+xlink:href="([^"]+)"\s*/>', lambda m: f"[{m.group(1)}]({m.group(1)})", result
    )
    result = re.sub(
        r'<link\s+linkend="([^"]+)"\s*/>', lambda m: f"[{m.group(1)}](#{m.group(1)})", result
    )
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
            if href:
                url = href.group(1) or href.group(2)
            else:
                # 无 href 的 <link linkend="X">：指向本教程内部章节（官网渲染为
                # 页间链接），序列化为 # 锚点保住链接语义，由前端决定怎么呈现
                anchor = re.search(r'linkend="([^"]+)"', link.group(2))
                url = f"#{anchor.group(1)}" if anchor else ""
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
