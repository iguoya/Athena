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
    element_text,
    load_structure,
    strip_tags,
)

CONTENT_CHAPTERS = PROJECT_ROOT / "content" / "chapters"


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def extract_blocks(fragment: str) -> list[dict]:
    """把节内容切成有序段流：para / listitem / code / heading（子节标题）。"""
    blocks: list[dict] = []

    def walk(source: str) -> None:
        # 子节标题与其内容交替出现：按第一层 section 切分，其余内容顺序扫描
        sections = direct_children("section", source)
        cursor = 0
        for sec_id, sec_frag in sections:
            sec_open = re.search(rf'<section(?:\s[^>]*)?xml:id="{re.escape(sec_id)}"', source[cursor:])
            if sec_open:
                sec_start = cursor + sec_open.start()
            else:
                sec_start = cursor
            emit_content(source[cursor:sec_start])
            heading_text = strip_tags(element_text("title", sec_frag, 0)[0])
            blocks.append({"type": "heading", "text": heading_text, "sha": sha(heading_text)})
            walk(sec_frag)
            sec_close = source.find("</section>", sec_start)
            cursor = sec_close + len("</section>") if sec_close != -1 else len(source)
        emit_content(source[cursor:])

    def emit_content(source: str) -> None:
        tag_re = re.compile(r"<(para|itemizedlist|programlisting|literallayout|figure)(?:\s[^>]*)?>")
        # 先收集列表区间：列表项内部的 para 由 itemizedlist 分支统一处理，避免重复成块
        list_spans: list[tuple[int, int]] = []
        for m in tag_re.finditer(source):
            if m.group(1) == "itemizedlist":
                _, list_end = element_text("itemizedlist", source, m.start())
                list_spans.append((m.start(), list_end))
        in_list = lambda pos: any(a <= pos < b for a, b in list_spans)
        for m in tag_re.finditer(source):
            kind = m.group(1)
            if kind == "para" and in_list(m.start()):
                continue
            if kind in ("para", "programlisting", "literallayout"):
                text, _ = element_text(kind, source, m.start())
                if kind == "para":
                    clean = strip_tags(text).strip()
                else:
                    # 代码块逐字保留缩进与空白，尊重原文（应用 ADR 0002）
                    clean = code_text(text)
                if not clean:
                    continue
                blocks.append({
                    "type": "code" if kind != "para" else "para",
                    "text": clean,
                    "sha": sha(clean),
                })
            elif kind == "itemizedlist":
                list_text, list_end = element_text("itemizedlist", source, m.start())
                for _, li_frag in direct_children("listitem", list_text):
                    li_text, _ = element_text("para", li_frag, 0)
                    clean = normalize(strip_tags(li_text if li_text else li_frag))
                    if clean:
                        blocks.append({"type": "listitem", "text": clean, "sha": sha(clean)})
            elif kind == "figure":
                fig_text, _ = element_text("figure", source, m.start())
                title = strip_tags(element_text("title", fig_text, 0)[0])
                if title:
                    blocks.append({"type": "figure", "text": title, "sha": sha(title)})

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
          old_zh: list[str] | None) -> tuple[list[dict], dict[str, int]]:
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
    else:
        # 首次生成：从旧 md 的中文段按序填充（para/listitem 一段对一段）
        zh_pool = list(old_zh or [])
        zh_iter = iter(zh_pool)
        for block in new_blocks:
            if block["type"] in ("code", "figure"):
                continue
            candidate = next(zh_iter, None)
            if candidate:
                block["zh"] = candidate
    return new_blocks, stats


def sync_section(chapter_id: str, section_id: str, section_title: str,
                 fragment: str, pinned: str) -> tuple[dict, dict]:
    out_path = CONTENT_CHAPTERS / chapter_id / f"{section_id}.json"
    old = None
    if out_path.is_file():
        old = json.loads(out_path.read_text(encoding="utf-8"))
    old_blocks = old.get("blocks") if old else None
    old_commit = old.get("upstream_commit") if old else None

    new_blocks = extract_blocks(fragment)
    md_path = out_path.with_suffix(".md")
    blocks, stats = align(old_blocks, new_blocks,
                          load_translation_from_md(md_path) if old is None else None)
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
        json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
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
    for chapter in structure:
        chapter_id = chapter["id"]
        source = DOCBOOK.read_text(encoding="utf-8")
        source = re.sub(r"<!--.*?-->", "", source, flags=re.S)
        for sec in chapter["sections"]:
            if args.section and sec["id"] != args.section:
                continue
            # 重新定位该节的原始片段（load_structure 只回了摘要）
            frag_match = re.search(
                rf'<section(?:\s[^>]*)?xml:id="{re.escape(sec["id"])}"', source)
            if frag_match is None:
                continue
            _, frag = next(
                (sid, f) for sid, f in direct_children("section", source[frag_match.start():])
                if sid == sec["id"])
            snapshot, stats = sync_section(
                chapter_id, sec["id"], re.sub(r"&(\w+);", "gtkmm", sec["title"]),
                frag, pinned["pinned_commit"])
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
