#!/usr/bin/env python3
"""上游同步：把官方 DocBook 的每节内容提取为**段落快照**，并自动对齐已有翻译。

这是「低负担追踪上游」方案的核心（应用 ADR 0002 的段落级追踪）：

- 原文不进任何手写文件。快照 `content/chapters/<章>/<节>.json` 由本脚本从
  upstream/gtkmm-documentation 的 index-in.docbook 生成并入库——上游一变，
  `git diff` 直接显示哪一段变了。
- 中文翻译按段挂在快照的 `zh` 字段上，是唯一的手写内容。
- 同步时用段落指纹（sha256）做 LCS 对齐（difflib）：指纹相同的段自动保留
  翻译；上游新增的段标 `untranslated`；内容变化的段标 `stale`（旧译文暂留，
  供参考）。**只有 stale/untranslated 的段需要动笔。**

用法：
    python scripts/sync_upstream.py                  # 全量同步到 pinned_commit
    python scripts/sync_upstream.py --section SEC    # 只同步一节
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_source import (  # noqa: E402
    DOCBOOK,
    PROJECT_ROOT,
    code_text,
    direct_children,
    docbook_entities,
    element_close,
    element_text,
    expand_entities,
    figure_ref,
    inline_md,
    load_structure,
    strip_tags,
)

_CUSTOM = docbook_entities()


def expand_md(raw: str) -> str:
    # 标准实体 + DocBook 自定义实体（gtkmm、cpp 等）一起展开
    return expand_entities(raw, _CUSTOM)

CONTENT_CHAPTERS = PROJECT_ROOT / "content" / "chapters"


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def inner_xml(fragment: str, element: str) -> str:
    """完整元素片段的内部 XML（element_text 的返回值本就是原始片段）。"""
    text, _ = element_text(element, fragment, 0)
    return text


def chapter_span(source: str, chapter_id: str) -> str | None:
    """章/附录元素的完整片段（含开闭标签）；找不到返回 None。"""
    m = re.search(rf'<(?:chapter|appendix)(?:\s[^>]*)?xml:id="{re.escape(chapter_id)}"', source)
    if m is None:
        return None
    end = element_close(source, m.start(), "chapter")
    if end == len(source):
        # element_close 按 "chapter" 扫描；附录元素名不同则再试
        end = element_close(source, m.start(), "appendix")
    return source[m.start():end]


def drop_first_title(fragment: str) -> str:
    """去掉片段中第一个 <title>…</title>（章标题不进正文块流）。"""
    m = re.search(r"<title(?:\s[^>]*)?>.*?</title>", fragment, re.S)
    return fragment[:m.start()] + fragment[m.end():] if m else fragment


def xref_titles(structure: list[dict], source: str) -> dict[str, str]:
    """linkend → 官网渲染文本（目标标题）：章节标题 + bridgehead 文本。"""
    titles: dict[str, str] = {}
    for chapter in structure:
        titles[chapter["id"]] = chapter["title"]
        for sec in chapter["sections"]:
            titles[sec["id"]] = sec["title"]
    for m in re.finditer(r"<bridgehead[^>]*xml:id=\"([^\"]+)\"[^>]*>(.*?)</bridgehead>",
                         source, re.S):
        titles[m.group(1)] = re.sub(r"\s+", " ", strip_tags(m.group(2))).strip()
    return titles


# 块级元素：官网渲染为独立结构。DocBook 允许它们嵌在 para 内部（SGML 遗留的
# 内容模型），XSLT 渲染时拆开——提取时同样拆出：混在 para 里的 screen 文本会被
# flow() 折叠成一坨，footnote 会被双重提取（所在 para 的文本含脚注 + 脚注 para
# 又独立成段），para 内嵌的列表会连同列表项一起并成一坨纯文本。
SPECIAL_RE = re.compile(
    r"<(screen|footnote|note|tip|warning|important|caution"
    r"|itemizedlist|orderedlist|variablelist|segmentedlist"
    r"|figure|screenshot|programlisting|literallayout)(?:\s[^>]*)?>")
ADMONITIONS = {"note", "tip", "warning", "important", "caution"}
FLOW_KINDS = {"itemizedlist", "orderedlist", "variablelist", "segmentedlist",
              "figure", "screenshot", "programlisting", "literallayout"}


def split_special(source: str) -> list[tuple[str | None, str]]:
    """把块级元素按文档顺序拆出：[(None, 普通片段) | (kind, 完整片段)]。

    拆分点落在 para 内部时，所在 para 按拆分点切开并补齐开闭标签——
    普通片段永远是平衡的 para（或非 para 内容），emit_flow 可以直接处理。
    """
    parts: list[tuple[str | None, str]] = []
    cursor, pos = 0, 0
    para_tail = False  # cursor 处于某个已被拆开的 para 的尾部（缺开标签）
    while True:
        m = SPECIAL_RE.search(source, pos)
        if m is None:
            break
        text, end = element_text(m.group(1), source, m.start())
        if not text:
            pos = m.end()  # 找不到闭合：当普通文本放行
            continue
        pre = source[cursor:m.start()]
        if para_tail:
            stop = pre.find("</para>")
            tail_text, rest = (pre[:stop], pre[stop + len("</para>"):]) \
                if stop != -1 else (pre, "")
            if tail_text.strip():
                parts.append((None, f"<para>{tail_text}</para>"))
            para_tail = False
            if rest:
                opens = len(re.findall(r"<para(?:\s[^>]*)?>", rest))
                if opens > rest.count("</para>"):
                    open_tag = re.search(r"<para(?:\s[^>]*)?>", rest)
                    parts.append((None, rest[:open_tag.end()] + "</para>"))
                    para_tail = True
                else:
                    parts.append((None, rest))
        elif len(re.findall(r"<para(?:\s[^>]*)?>", pre)) > pre.count("</para>"):
            parts.append((None, pre + "</para>"))
            para_tail = True
        elif pre:
            parts.append((None, pre))
        parts.append((m.group(1), source[m.start():end]))
        cursor = pos = end
    tail = source[cursor:]
    if para_tail:
        if tail.strip():
            parts.append((None, f"<para>{tail}</para>"))
    elif tail:
        parts.append((None, tail))
    return parts


def extract_blocks(fragment: str) -> list[dict]:
    """把节内容切成有序段流：para / listitem / code / heading / figure。"""
    blocks: list[dict] = []

    def walk(source: str) -> None:
        # 子节标题与其内容交替出现：按第一层 section 切分，其余内容顺序扫描
        sections = direct_children("section", source)
        cursor = 0
        for sec_id, sec_frag in sections:
            if sec_id is not None:
                sec_open = re.search(
                    rf'<section(?:\s[^>]*)?xml:id="{re.escape(sec_id)}"', source[cursor:])
            else:
                sec_open = re.search(r"<section(?:\s[^>]*)?>", source[cursor:])
            sec_start = cursor + sec_open.start() if sec_open else cursor
            emit_content(source[cursor:sec_start])
            heading_text = strip_tags(element_text("title", sec_frag, 0)[0])
            blocks.append({"type": "heading", "text": heading_text, "sha": sha(heading_text)})
            walk(sec_frag)
            # 该 child 自己的闭合：深度扫描定位——find 找第一个 </section> 会
            # 停在嵌套子节的闭合，导致剩余内容被下一轮重复处理（重复块）
            cursor = element_close(source, sec_start, "section")
        emit_content(source[cursor:])

    def emit_content(source: str) -> None:
        for kind, part in split_special(source):
            if kind is None:
                emit_flow(part)
            elif kind == "screen":
                inner = inner_xml(part, "screen")
                clean = code_text(inner)
                if clean:
                    blocks.append({"type": "code", "text": clean, "sha": sha(clean)})
            elif kind == "footnote":
                emit_content(inner_xml(part, "footnote"))
            elif kind in ADMONITIONS:
                # admonition：内部照常提取，产出的块统一打上类型（渲染成提示框）
                start = len(blocks)
                emit_content(inner_xml(part, kind))
                for block in blocks[start:]:
                    block["admonition"] = kind
            else:
                # 提升/顶层的列表、图、程序清单：按原有 emit_flow 分支处理
                emit_flow(part)

    def emit_flow(source: str) -> None:
        tag_re = re.compile(
            r"<(para|simpara|itemizedlist|orderedlist|variablelist|segmentedlist"
            r"|programlisting|literallayout|figure|screenshot|bridgehead)(?:\s[^>]*)?>")
        # 先收集区间：列表项内部的 para 由列表分支统一处理；figure 内的
        # screenshot 不再单独成块（figure 分支已提取同一张图）
        spans: list[tuple[int, int, str]] = []
        for m in tag_re.finditer(source):
            if m.group(1) in ("itemizedlist", "orderedlist", "variablelist",
                              "segmentedlist", "figure"):
                _, span_end = element_text(m.group(1), source, m.start())
                spans.append((m.start(), span_end, m.group(1)))
        def inside(pos: int, *kinds: str) -> bool:
            return any(a <= pos < b and k in kinds for a, b, k in spans)
        for m in tag_re.finditer(source):
            kind = m.group(1)
            if kind in ("para", "simpara") and inside(m.start(),
                    "itemizedlist", "orderedlist", "variablelist", "segmentedlist"):
                continue
            if kind in ("para", "simpara", "programlisting", "literallayout"):
                text, _ = element_text(kind, source, m.start())
                if kind in ("para", "simpara"):
                    # 正文保留内联格式（粗/斜/行内代码/链接）；指纹严格沿用旧口径
                    # （strip_tags 纯文本）——已有翻译不因格式升级而失效（ADR 0002）
                    key = sha(strip_tags(text).strip())
                    clean = inline_md(expand_md(text)).strip()
                else:
                    # 代码块逐字保留缩进与空白，尊重原文（应用 ADR 0002）
                    clean = code_text(text)
                    key = sha(clean)
                if not clean:
                    continue
                blocks.append({
                    "type": "code" if kind not in ("para", "simpara") else "para",
                    "text": clean,
                    "sha": key,
                })
            elif kind in ("itemizedlist", "orderedlist"):
                list_text, _ = element_text(kind, source, m.start())
                for index, (_, li_frag) in enumerate(direct_children("listitem", list_text), 1):
                    li_text, _ = element_text("para", li_frag, 0)
                    if not li_text:
                        li_text, _ = element_text("simpara", li_frag, 0)
                    raw = li_text if li_text else li_frag
                    # 列表项同样保留内联格式（链接/粗斜体/行内代码）；
                    # 无序列表项沿用列表项指纹口径；有序列表项沿用段落口径——
                    # 这批段此前被当作 para 提取，口径一致才不丢已有翻译
                    clean = inline_md(expand_md(raw)).strip()
                    if not clean:
                        continue
                    block = {"type": "listitem", "text": clean}
                    if kind == "itemizedlist":
                        block["sha"] = sha(normalize(strip_tags(raw)))
                    else:
                        block["sha"] = sha(strip_tags(raw).strip())
                        block["marker"] = f"{index}."
                    blocks.append(block)
            elif kind == "variablelist":
                # 官网渲染：term 加粗行 + 缩进描述。受限块模型下 term 走 marker
                # （纯文本，渲染在项首加粗位），desc 走 text 且沿用段落指纹口径——
                # 这批描述此前被当作 para 提取，口径一致才不丢已有翻译
                list_text, _ = element_text("variablelist", source, m.start())
                for _, entry_frag in direct_children("varlistentry", list_text):
                    term_text, _ = element_text("term", entry_frag, 0)
                    li_frags = direct_children("listitem", entry_frag)
                    li_frag = li_frags[0][1] if li_frags else entry_frag
                    desc, _ = element_text("para", li_frag, 0)
                    if not desc:
                        desc, _ = element_text("simpara", li_frag, 0)
                    raw = desc if desc else li_frag
                    clean = inline_md(expand_md(raw)).strip()
                    if not clean:
                        continue
                    blocks.append({"type": "listitem", "text": clean,
                                   "sha": sha(strip_tags(raw).strip()),
                                   "marker": strip_tags(term_text).strip()})
            elif kind == "segmentedlist":
                # 官网渲染为两列表格（segtitle 为表头）：受限块模型下每行一块；
                # seg 的内容是代码标识符，inline_md 已序列化为行内代码，直接拼接
                list_text, _ = element_text("segmentedlist", source, m.start())
                titles = [inline_md(expand_md(strip_tags(t)))
                          for t in re.findall(r"<segtitle(?:\s[^>]*)?>(.*?)</segtitle>",
                                              list_text, re.S)]
                header = " → ".join(titles)
                if header:
                    blocks.append({"type": "listitem", "text": header,
                                   "sha": sha(normalize(header))})
                for _, item_frag in direct_children("seglistitem", list_text):
                    segs = [inline_md(expand_md(strip_tags(s))) for s in
                            re.findall(r"<seg(?:\s[^>]*)?>(.*?)</seg>", item_frag, re.S)]
                    clean = " → ".join(s for s in segs if s)
                    if clean:
                        blocks.append({"type": "listitem", "text": clean,
                                       "sha": sha(normalize(strip_tags(item_frag)))})
            elif kind == "figure":
                fig_text, fig_end = element_text("figure", source, m.start())
                title = strip_tags(element_text("title", fig_text, 0)[0])
                if title:
                    ref = figure_ref(expand_md(fig_text))
                    blocks.append({"type": "figure", "text": title,
                                   "ref": ref, "sha": sha(title)})
            elif kind == "screenshot":
                # 不在 figure 里的游离截图（cairo 时钟、文件对话框）：无题注
                if inside(m.start(), "figure"):
                    continue
                shot_text, _ = element_text("screenshot", source, m.start())
                ref = figure_ref(expand_md(shot_text))
                if ref:
                    blocks.append({"type": "figure", "text": "",
                                   "ref": ref, "sha": sha("screenshot:" + ref)})
            elif kind == "bridgehead":
                head_text, _ = element_text("bridgehead", source, m.start())
                text = strip_tags(head_text)
                if text:
                    blocks.append({"type": "heading", "text": text, "sha": sha(text)})

    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    walk(fragment)
    # 去重指纹碰撞（同文段落）：sha 加序号后缀
    seen: dict[str, int] = {}
    for block in blocks:
        key = block["sha"]
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            block["sha"] = f"{key}-{seen[key] - 1}"
    return blocks


def load_translation_from_md(md_path: Path) -> list[str]:
    """从旧对照稿 md 抽取中文段。md 段落以空行分隔，连续行合并为一段。"""
    if not md_path.is_file():
        return []
    text = md_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    text = re.sub(r"^---\n[\s\S]*?\n---\n", "", text)
    text = re.sub(r"<!--[\s\S]*?-->\n?", "", text)
    zh: list[str] = []
    in_code = False
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            zh.append(re.sub(r"\s+", " ", " ".join(paragraph)).strip())
            paragraph.clear()

    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            flush()
            continue
        if in_code:
            continue
        if line.startswith("#") or line.startswith(">"):
            flush()
            continue
        if line.startswith("- "):
            flush()
            zh.append(line[2:].strip())
            continue
        if line.strip():
            paragraph.append(line.strip())
        else:
            flush()
    flush()
    return zh


def align(old_blocks: list[dict] | None, new_blocks: list[dict],
          old_zh: list[str] | None = None) -> tuple[list[dict], dict[str, int]]:
    """LCS 对齐：指纹相同即同一段，保留 zh；新段 untranslated；变段 stale。"""
    for index, block in enumerate(new_blocks):
        if block["type"] == "code" or block["type"] == "figure":
            block["zh"] = ""
        else:
            block["zh"] = None

    stats = {"kept": 0, "stale": 0, "new": 0, "gone": 0}
    if old_blocks:
        old_keys = [b["sha"] for b in old_blocks]
        new_keys = [b["sha"] for b in new_blocks]
        matcher = difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    old_b, new_b = old_blocks[i1 + k], new_blocks[j1 + k]
                    if new_b["type"] not in ("code", "figure"):
                        new_b["zh"] = old_b.get("zh")
                        if new_b.get("stale_from"):
                            new_b["stale_from"] = old_b.get("stale_from")
                stats["kept"] += i2 - i1
            elif tag == "replace":
                # 指纹不同 = 原文被改：新段标 stale，旧译文暂留 stale_from 供参考
                changed = 0
                for k in range(j2 - j1):
                    new_b = new_blocks[j1 + k]
                    if new_b["type"] in ("code", "figure"):
                        continue  # 代码/图题照录原文，无译文可失效
                    counterpart = old_blocks[i1 + k] if k < (i2 - i1) else None
                    new_b["status"] = "stale"
                    if counterpart and counterpart.get("zh"):
                        new_b["stale_from"] = counterpart["zh"]
                    if not new_b.get("zh"):
                        new_b["zh"] = None
                    changed += 1
                stats["stale"] += changed
            elif tag == "insert":
                for k in range(j2 - j1):
                    new_b = new_blocks[j1 + k]
                    if new_b["type"] not in ("code", "figure"):
                        new_b["status"] = "untranslated"
                stats["new"] += j2 - j1
            elif tag == "delete":
                stats["gone"] += i2 - i1
    # 首次生成不做顺序填充——按序对齐正是错位事故的源头（应用 ADR 0002 复盘）。
    # 译文一律内容寻址填充：apply_po.py（官方 po 指纹）或人工按段前缀匹配。
    return new_blocks, stats


def preamble_blocks(source: str, chapter_id: str) -> list[dict]:
    """章导语块：与正文同一套提取机制（列表/提示框/终端块全覆盖），
    但 para 指纹沿用导语通道的历史口径（折叠全部空白）——已有导语译文
    不因通道合并而变 stale。"""
    from inline_md import strip_inline_md
    fragment = chapter_preamble_fragment(source, chapter_id)
    if not fragment:
        return []
    blocks = extract_blocks(fragment)
    for block in blocks:
        if block["type"] == "para":
            block["sha"] = sha(re.sub(r"\s+", " ", strip_inline_md(block["text"])).strip())
    return blocks


def chapter_preamble_fragment(source: str, chapter_id: str) -> str:
    """章导语片段：章标题之后、第一个 section 之前的 XML（官网章页头部）。"""
    m = re.search(rf'<chapter(?:\s[^>]*)?xml:id="{re.escape(chapter_id)}"', source)
    if m is None:
        return ""
    depth, inner_start = 1, m.end()
    tag_re = re.compile(r"</?chapter(?:\s[^>]*)?>")
    end = len(source)
    for t in tag_re.finditer(source, m.end()):
        depth += 1 if not t.group(0).startswith("</") else -1
        if depth == 0:
            end = t.start()
            break
    frag = source[inner_start:end]
    sec_open = re.search(r"<section[\s>]", frag)
    head = frag[: sec_open.start()] if sec_open else frag
    title_end = head.find("</title>")
    if title_end != -1:
        head = head[title_end + len("</title>"):]
    return head


def strip_meta_labels(blocks: list[dict]) -> list[dict]:
    """元标签结构化（应用 ADR 0002）：DocBook 的「Source Code」「File: xxx」
    是代码块的结构性标记，不是正文——提取时消化：
    - 「Source Code」段丢弃（信息 = 后面有代码，代码块自身可表意）；
    - 「File: xxx」段转化为紧随代码块的 file 属性（渲染为代码块标题）。
    元标签不再以正文段形态出现在快照中。"""
    out: list[dict] = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b["type"] == "para":
            plain = re.sub(r"\s+", " ", b["text"]).strip()
            if plain == "Source Code":
                i += 1
                continue
            link = re.match(r"^\[Source Code\]\(([^)]+)\)$", plain)
            if link:
                # 官网 2026 版：Source Code 是指向源码的链接——把 URL 附给
                # 本节内下一个代码块（渲染为「完整源码 ↗」），链接段本身消化
                for j in range(i + 1, len(blocks)):
                    if blocks[j]["type"] == "code":
                        blocks[j] = {**blocks[j], "source_url": link.group(1)}
                        break
                i += 1
                continue
            m = re.match(r"^File:\s*(.+?)(?:\s*\((?:For use with[^)]*|gtkmm [234][^)]*)\))?$", plain)
            if m and i + 1 < len(blocks) and blocks[i + 1]["type"] == "code":
                out.append({**blocks[i + 1], "file": m.group(1).strip()})
                i += 2
                continue
        out.append(b)
        i += 1
    return out


def sync_section(chapter_id: str, section_id: str, section_title: str,
                 fragment: str, pinned: str,
                 preamble_blocks: list[dict] | None = None) -> tuple[dict, dict]:
    out_path = CONTENT_CHAPTERS / chapter_id / f"{section_id}.json"
    old = None
    if out_path.is_file():
        old = json.loads(out_path.read_text(encoding="utf-8"))
    old_blocks = old.get("blocks") if old else None
    old_commit = old.get("upstream_commit") if old else None

    # 官网章页 = 章导语 + 第一节：导语块并入第一节开头（应用 ADR 0002）
    new_blocks = strip_meta_labels(list(preamble_blocks or []) + extract_blocks(fragment))
    md_path = out_path.with_suffix(".md")
    blocks, stats = align(old_blocks, new_blocks)
    snapshot = {
        "chapter": chapter_id,
        "section": section_id,
        "title": section_title,
        "upstream_commit": pinned,
        "blocks": blocks,
    }
    if old_blocks is not None and json.dumps(old_blocks, ensure_ascii=False) == json.dumps(blocks, ensure_ascii=False):
        # 提取结果与现状完全一致：保持原文件不动，避免噪声 diff
        return snapshot, stats
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")
    return snapshot, stats


def main() -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="同步上游段落快照并对齐翻译")
    parser.add_argument("--section", help="只同步指定节 id")
    args = parser.parse_args()

    pinned = json.loads((PROJECT_ROOT / "upstream.json").read_text(encoding="utf-8"))
    if not DOCBOOK.is_file():
        raise SystemExit("upstream/gtkmm-documentation 不存在，先克隆官方仓库（见 AGENTS.md）")

    structure = load_structure()
    totals = {"kept": 0, "stale": 0, "new": 0, "gone": 0}
    synced = 0
    source = DOCBOOK.read_text(encoding="utf-8")
    source = re.sub(r"<!--.*?-->", "", source, flags=re.S)
    # <xref linkend="X"/> 官网渲染为指向目标的链接（文本 = 目标标题）；
    # 提取前替换成受限 markdown 链接，正文不留「剥标签后的空洞」
    titles = xref_titles(structure, source)
    source = re.sub(
        r"<xref\s+linkend=\"([^\"]+)\"\s*/>",
        lambda m: f"[{titles.get(m.group(1), m.group(1))}](#{m.group(1)})",
        source)
    for chapter in structure:
        chapter_id = chapter["id"]
        for sec in chapter["sections"]:
            if args.section and sec["id"] != args.section:
                continue
            # 重新定位该节的原始片段（load_structure 只回了摘要）
            frag_match = re.search(
                rf'<section(?:\s[^>]*)?xml:id="{re.escape(sec["id"])}"', source)
            preamble: list[dict] = []
            if frag_match is not None:
                # 章导语：章标题之后、第一个节之前的段流，并入第一节（官网章页行为）
                if sec["id"] == chapter["sections"][0]["id"]:
                    preamble = preamble_blocks(source, chapter_id)
                _, frag = next(
                    (sid, f) for sid, f in direct_children("section", source[frag_match.start():])
                    if sid == sec["id"])
            elif sec["id"] == chapter_id:
                # 单页章：节 id = 章 id，没有 section 分页——整章即内容，
                # 导语已在其中，不再叠加 preamble（会重复）
                whole = chapter_span(source, chapter_id)
                if whole is None:
                    continue
                frag = drop_first_title(whole)
            else:
                continue
            snapshot, stats = sync_section(
                chapter_id, sec["id"], re.sub(r"&(\w+);", "gtkmm", sec["title"]),
                frag, pinned["pinned_commit"], preamble)
            for key in totals:
                totals[key] += stats[key]
            synced += 1
            pending = sum(1 for b in snapshot["blocks"]
                          if b.get("status") in ("stale", "untranslated"))
            flag = " ←有待译" if pending else ""
            print(f"{chapter_id}/{sec['id']}: {len(snapshot['blocks'])} 段{flag}")
    print(
        f"\n同步 {synced} 节：保留译文 {totals['kept']} 段、原文已变 {totals['stale']} 段、"
        f"新增 {totals['new']} 段、上游删除 {totals['gone']} 段"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
