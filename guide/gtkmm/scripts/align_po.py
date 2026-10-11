#!/usr/bin/env python3
"""PO 翻译单元 ↔ 快照段落区间对齐（应用 ADR 0005）。

apply_po.py 的指纹是「整条 msgid ↔ 单个段落」，官网 PO 经常把连续几个
段落合并成一条翻译单元，这类条目永远对不上（译文挂不上、导出覆盖不了）。
本脚本把每节快照的连续文字段做成「区间拼接指纹」（连续 1..n 段的
snapshot_plain 以空格连接），再拿每条 PO msgid 的纯文本指纹去精确匹配——
单段与多段条目都能对齐。

产出：content/po-units/<章>.json
    { "<节>": [ { "id": <单元首段 sha>, "shas": [...], "zh": <整条官方译文|null> } ] }
- id 即前端「阅读单元」的锚点（unitSha = blocks[0].sha，与「看懂了」同口径）；
- zh 是整条官方译文（po_to_plain 纯文本口径），多段单元不再拆挂到段；
- 消费方：PageView（按单元分组显示）、export_contribution.py（单元级导出）。

只读快照与 po，不写快照；重新生成直接重跑本脚本（sync_upstream 之后跑）。

用法：
    python scripts/align_po.py            # 生成映射并打印覆盖率
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_po import CHAPTERS, PO, REFERENCE_PO, parse_po, po_to_plain, snapshot_plain  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "content" / "po-units"
# 快照里的非文字块：PO 段落单元不会跨越它们，对齐区间在这里截断
BREAK_TYPES = {"heading", "code", "figure"}


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def build_interval_index() -> dict[str, dict]:
    """全部快照的连续文字段区间指纹 → {chapter, page, shas}。

    节内按 run（连续 para/listitem，遇标题/代码/图截断）枚举所有
    连续区间；同指纹撞键先到先得（与 apply_po 的 setdefault 口径一致）。"""
    index: dict[str, dict] = {}
    for path in sorted(CHAPTERS.rglob("*.json")):
        chapter = path.parent.name
        page = path.stem
        data = json.loads(path.read_text(encoding="utf-8"))
        run: list[dict] = []
        runs: list[list[dict]] = []
        for block in data["blocks"]:
            if block["type"] in ("para", "listitem"):
                run.append(block)
            else:
                if run:
                    runs.append(run)
                    run = []
        if run:
            runs.append(run)
        for blocks in runs:
            prints = [snapshot_plain(b["text"]) for b in blocks]
            shas = [b["sha"] for b in blocks]
            n = len(prints)
            for i in range(n):
                acc = ""
                for j in range(i, n):
                    acc = f"{acc} {prints[j]}".strip()
                    # 同一指纹可能撞上重复措辞的段落区间：保持先到先得
                    index.setdefault(
                        acc, {"chapter": chapter, "page": page, "shas": shas[i : j + 1]}
                    )
    return index


def main() -> int:
    force_utf8()
    po_source = REFERENCE_PO if REFERENCE_PO.is_file() else PO
    entries = parse_po(po_source.read_text(encoding="utf-8"))
    index = build_interval_index()

    # 章 → 节 → 单元列表；id 锚定首段 sha（unitSha 口径）
    units_by_chapter: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    matched_paras = 0
    single = multi = empty_zh = 0
    for msgid, msgstr in entries.items():
        plain = po_to_plain(msgid)
        hit = index.get(plain)
        if hit is None:
            continue
        zh = po_to_plain(msgstr) if msgstr.strip() else None
        if zh is None:
            empty_zh += 1
        unit = {"id": hit["shas"][0], "shas": hit["shas"], "zh": zh}
        units_by_chapter[hit["chapter"]][hit["page"]].append(unit)
        matched_paras += len(hit["shas"])
        if len(hit["shas"]) == 1:
            single += 1
        else:
            multi += 1

    OUT_DIR.mkdir(exist_ok=True)
    for chapter, pages in units_by_chapter.items():
        out = OUT_DIR / f"{chapter}.json"
        out.write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")

    total = sum(
        1
        for path in CHAPTERS.rglob("*.json")
        for b in json.loads(path.read_text(encoding="utf-8"))["blocks"]
        if b["type"] in ("para", "listitem")
    )
    print(f"PO 源：{po_source.name}；条目 {len(entries)}，对齐单元 {single + multi}"
          f"（单段 {single}、多段 {multi}），覆盖段落 {matched_paras}/{total}")
    print(f"其中官方暂无译文的单元 {empty_zh} 个（显示待译、留给自译）")
    print(f"映射已写入 {OUT_DIR.relative_to(PROJECT_ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
