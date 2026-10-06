#!/usr/bin/env python3
"""从本地克隆的官方仓库提取教程结构，为翻译稿生成可校验的源基准。

官方仓库：https://gitlab.gnome.org/GNOME/gtkmm-documentation（克隆在
upstream/gtkmm-documentation，gitignore，不入库）。文档源是单个 DocBook：
docs/tutorial/C/index-in.docbook；官网的「每节一页」由 XSLT chunking 生成，
分页单元 = 章下第一层 <section>（章的直接导语并入第一个单元开头，子节留页内）。

每个单元的规范化文本算 sha256，翻译稿头部记录该值；check.py 重新计算并比对，
上游改动原文即报警「待复核」——这是「严格追踪上游、动态更新翻译」的落地机制。

用法：
    python scripts/extract_source.py --list            # 全部章/节结构 + sha
    python scripts/extract_source.py --section SEC_ID  # 打印某节规范化原文
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCBOOK = (PROJECT_ROOT / "upstream" / "gtkmm-documentation"
           / "docs" / "tutorial" / "C" / "index-in.docbook")


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


_ENTITY_CACHE: dict[str, str] | None = None


def docbook_entities() -> dict[str, str]:
    """DocBook 头部 <!ENTITY name "value"> 的实体表；value 里的标签剥成纯文本。"""
    global _ENTITY_CACHE
    if _ENTITY_CACHE is not None:
        return _ENTITY_CACHE
    source = DOCBOOK.read_text(encoding="utf-8")
    entities: dict[str, str] = {}
    for m in re.finditer(r'<!ENTITY ([\w-]+)\s+"([^"]*)"\s*>', source):
        value = re.sub(r"<[^>]+>", "", m.group(2))
        entities[m.group(1)] = value
    _ENTITY_CACHE = entities
    return entities


def strip_tags(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    # DocBook 实体（html.unescape 覆盖常用集；docbook 自定义实体从文件头解析）
    entities = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
                "&apos;": "'", "&mdash;": "—", "&nbsp;": " ",
                "&uuml;": "ü", "&szlig;": "ß", "&copy;": "©",
                "&nbhy;": "‑"}
    entities.update({f"&{name};": value for name, value in docbook_entities().items()})
    for entity, char in entities.items():
        text = text.replace(entity, char)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return text.strip()


def code_text(raw: str) -> str:
    """程序清单的清洗：剥标签、展开实体、去首尾空行，**逐字保留缩进与内部空白**。

    代码是原文的一部分（应用 ADR 0002）：任何空白规整都是对原文的篡改，
    与 strip_tags 的段落规整刻意分开。
    """
    text = re.sub(r"<[^>]+>", "", raw)
    entities = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
                "&apos;": "'", "&nbsp;": " "}
    entities.update({f"&{name};": value for name, value in docbook_entities().items()})
    for entity, char in entities.items():
        text = text.replace(entity, char)
    return text.strip("\n")



# 内联格式序列化：DocBook 行内标签 → 受限 markdown。
# 不变量：strip_inline_md(序列化结果) == strip_tags(原文)，保证段落指纹稳定、
# 已有翻译在重新提取时不失效（应用 ADR 0002 的格式保真升级）。
_MD_CODE_TAGS = {"code", "command", "filename", "literal", "classname",
                 "typename", "constant", "function", "replaceable",
                 "parameter", "application", "systemitem", "guilabel",
                 "guimenuitem", "option", "varname", "structname", "type"}


def _innermost(tag: str, source: str):
    """找最内层的 <tag>...</tag> 片段（内部不含同名标签）。"""
    pattern = re.compile(rf"<{tag}(\s[^>]*)?>((?:(?!<{tag}[\s>]|</{tag}>).)*)</{tag}>", re.S)
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
                result = result[:m.start()] + f"`{inner}`" + result[m.end():]
                changed = True
        for m in re.finditer(r'<emphasis([^>]*)>((?:(?!<emphasis[\s>]|</emphasis>).)*)</emphasis>', result, re.S):
            role = re.search(r'role="(\w+)"', m.group(1))
            inner = inline_md(m.group(2))
            mark = "**" if role and role.group(1) == "bold" else "*"
            result = result[:m.start()] + f"{mark}{inner}{mark}" + result[m.end():]
            changed = True
            break
        for m in re.finditer(r'<(link|ulink)([^>]*)>((?:(?!<[\s>]|</>).)*)</>', result, re.S):
            href = re.search(r'xlink:href="([^"]+)"|href="([^"]+)"', m.group(2))
            url = (href.group(1) or href.group(2)) if href else ""
            inner = inline_md(m.group(3))
            result = result[:m.start()] + f"[{inner}]({url})" + result[m.end():]
            changed = True
            break
        if not changed:
            break
    # quote 与其余未知标签剥壳保文本（不改变指纹）
    result = re.sub(r"</?(?:quote|citetitle|accel|keycap|keycombo|mousebutton|html:[a-z]+)(?:\s[^>]*)?>", "", result)
    result = re.sub(r"<[^>]+>", "", result)
    return result


def strip_inline_md(text: str) -> str:
    """把受限 markdown 还原成纯文本（指纹计算的规范化输入）。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    return text


def expand_entities(text: str) -> str:
    """只展开实体（含值内含标签的 DocBook 自定义实体），保留其余标签。"""
    for name, value in sorted(docbook_entities().items(), key=lambda kv: -len(kv[0])):
        text = text.replace(f"&{name};", value)
    for entity, char in {"&amp;": "&", "&lt;": "<", "&gt;": ">",
                         "&quot;": '"', "&apos;": "'", "&nbsp;": " ",
                         "&uuml;": "ü", "&szlig;": "ß", "&copy;": "©",
                         "&nbhy;": "‑"}.items():
        text = text.replace(entity, char)
    return text


def figure_ref(source: str) -> str | None:
    m = re.search(r'fileref="([^"]+)"', source)
    return m.group(1) if m else None


def normalize(text: str) -> str:
    """规范化：段内空白折叠、段间统一单换行——上游微调空白不应触发误报。"""
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def element_text(element: str, source: str, start: int) -> tuple[str, int]:
    """取 element 从 start 开始的完整文本（处理同名嵌套），返回 (文本, 结束位置)。"""
    open_re = re.compile(rf"<{element}(?:\s[^>]*)?>")
    match = open_re.search(source, start)
    if match is None:
        return "", start
    depth, cursor = 1, match.end()
    tag_re = re.compile(rf"</?{element}(?:\s[^>]*)?>")
    for m in tag_re.finditer(source, match.end()):
        depth += 1 if not m.group(0).startswith("</") else -1
        if depth == 0:
            return source[match.end():m.start()], m.end()
    return source[cursor:], len(source)


def direct_children(element: str, source: str) -> list[tuple[str | None, str]]:
    """source 里 element 的直接子元素（同名嵌套不误判），返回 [(xml_id, 内容)]。"""
    children: list[tuple[str | None, str]] = []
    open_re = re.compile(rf"<{element}(?:\s[^>]*)?>")
    tag_re = re.compile(rf"</?{element}(?:\s[^>]*)?>")
    cursor = 0
    while True:
        match = open_re.search(source, cursor)
        if match is None:
            break
        id_match = re.search(r'xml:id="([^"]+)"', match.group(0))
        depth, inner_start = 1, match.end()
        end = inner_start
        for m in tag_re.finditer(source, match.end()):
            depth += 1 if not m.group(0).startswith("</") else -1
            if depth == 0:
                end = m.start()
                break
        children.append((id_match.group(1) if id_match else None,
                         source[inner_start:end]))
        cursor = end
        tag_close = source.find(f"</{element}>", cursor)
        if tag_close == -1:
            break
        cursor = tag_close
    return children


def title_of(fragment: str) -> str:
    text, _ = element_text("title", fragment, 0)
    return strip_tags(text)


def body_text(fragment: str) -> str:
    """节内容的规范化文本：去掉 title，保留 para/程序清单/列表的阅读顺序。"""
    open_title = re.search(r"<title(?:\s[^>]*)?>", fragment)
    if open_title:
        _, title_end = element_text("title", fragment, open_title.start())
        after_title = fragment[title_end:]
    else:
        after_title = fragment
    parts: list[str] = []
    cursor = 0
    tag_re = re.compile(r"<(para|programlisting|literallayout|listitem)(?:\s[^>]*)?>")
    for m in tag_re.finditer(after_title):
        text, end = element_text(m.group(1), after_title, m.start())
        if m.group(1) in ("programlisting", "literallayout"):
            parts.append("[code]\n" + strip_tags(text) + "\n[/code]")
        else:
            cleaned = normalize(strip_tags(text))
            if cleaned:
                parts.append(cleaned)
        cursor = max(cursor, end)
    return "\n".join(parts)


def load_structure() -> list[dict]:
    source = DOCBOOK.read_text(encoding="utf-8")
    source = re.sub(r"<!--.*?-->", "", source, flags=re.S)  # 文件头注释里嵌着标签字面量
    structure: list[dict] = []
    for xml_id, fragment in direct_children("chapter", source):
        if xml_id is None:
            continue
        preamble = ""
        first_section = direct_children("section", fragment)
        head = fragment[:fragment.find("<section")] if first_section else fragment
        head_text = body_text(head)
        if head_text:
            preamble = head_text
        units = []
        for index, (sec_id, sec_frag) in enumerate(first_section):
            text = body_text(sec_frag)
            if index == 0 and preamble:
                text = preamble + "\n" + text
            units.append({
                "id": sec_id,
                "title": title_of(sec_frag),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            })
        structure.append({"id": xml_id, "title": title_of(fragment), "sections": units})
    for xml_id, fragment in direct_children("appendix", source):
        if xml_id is None:
            continue
        units = [{"id": sid, "title": title_of(frag),
                  "sha256": hashlib.sha256(body_text(frag).encode("utf-8")).hexdigest()}
                 for sid, frag in direct_children("section", fragment)]
        structure.append({"id": xml_id, "title": title_of(fragment),
                          "sections": units, "appendix": True})
    return structure


def main() -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="提取官方教程结构与源 hash")
    parser.add_argument("--list", action="store_true", help="列出章/节结构与 sha")
    parser.add_argument("--section", help="打印某节规范化原文")
    parser.add_argument("--json", help="把结构写入 JSON 文件")
    args = parser.parse_args()

    if not DOCBOOK.is_file():
        raise SystemExit(
            f"找不到官方文档源：{DOCBOOK}\n"
            "先克隆官方仓库：git clone https://gitlab.gnome.org/GNOME/gtkmm-documentation.git "
            "upstream/gtkmm-documentation（在应用根 subjects/gtkmm/ 下执行）"
        )
    if args.section:
        for chapter in load_structure():
            for unit in chapter["sections"]:
                if unit["id"] == args.section:
                    print(unit["sha256"])
                    print(unit["title"])
                    return 0
        raise SystemExit(f"未找到节：{args.section}")

    structure = load_structure()
    if args.json:
        Path(args.json).write_text(
            json.dumps(structure, ensure_ascii=False, indent=1), encoding="utf-8")
    chapters = sum(1 for c in structure)
    sections = sum(len(c["sections"]) for c in structure)
    print(f"上游结构：{chapters} 个单元（含附录）、{sections} 个分页节")
    if args.list:
        for chapter in structure:
            print(f"# {chapter['id']}  {chapter['title']}")
            for unit in chapter["sections"]:
                print(f"    {unit['id']}  {unit['sha256'][:12]}  {unit['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
