#!/usr/bin/env python3
"""从快照反向生成标准 po 贡献文件：反哺上游 / Damned Lies 的产出工具。

做法：以基准 po（po/reference.zh_CN.po，官方模板的最新翻译状态）为骨架——
msgid/位置/注释全部保留原样——只把「我们有更好译文」的条目替换 msgstr：

- 覆盖改进：基准里空或 fuzzy 的条目，若快照指纹命中则填入我们的译文（并摘除 fuzzy）；
- 质量修订：基准已有译文但与快照译文不同 → 默认保留基准（尊重上游社区译文），
  我们的译文写入随附的「贡献清单」供人工对照，人工确认更优的可手工替换。

输出：
  po/contribution.zh_CN.po   可直接上传 Damned Lies / 提 MR 的贡献文件
  po/contribution-report.json 条目级清单（本批改了哪些条目、改动类型），供人工过目

用法：
    python scripts/export_contribution.py            # 生成贡献文件与清单
    python scripts/export_contribution.py --apply    # 同上（当前两模式等价，保留一致性）
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_po import parse_po, po_to_plain, snapshot_plain  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REF_PO = PROJECT_ROOT / "po" / "reference.zh_CN.po"
CHAPTERS = PROJECT_ROOT / "content" / "chapters"
OUT_PO = PROJECT_ROOT / "po" / "contribution.zh_CN.po"
OUT_REPORT = PROJECT_ROOT / "po" / "contribution-report.json"


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def snapshot_plain(text: str) -> str:
    """快照段（内联 markdown）→ 纯文本指纹口径。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def po_plain(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    for entity, char in {"&amp;": "&", "&lt;": "<", "&gt;": ">",
                         "&quot;": '"', "&apos;": "'", "&nbsp;": " "}.items():
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    force_utf8()
    ref_text = REF_PO.read_text(encoding="utf-8")

    # ---- 快照译文集合（纯文本指纹 → 中文）----
    snap_zh: dict[str, str] = {}
    for f in sorted(CHAPTERS.rglob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for block in data["blocks"]:
            if block["type"] in ("para", "listitem") and block.get("zh"):
                key = snapshot_plain(block["text"])
                snap_zh.setdefault(key, block["zh"])

    # ---- 逐块改写 ref po：只动 msgstr ----
    blocks = re.split(r"(\n\s*\n)", ref_text)
    improved = fuzzy_fixed = 0
    report: list[dict] = []

    for block in blocks:
        if "msgid" not in block:
            continue
        mid_m = re.search(r'msgid ((?:(?!\nmsgstr).|\n)+)', block)
        mstr_m = re.search(r'msgstr ((?:(?!\nmsgstr).|\n)+)', block)
        if not mid_m or not mstr_m:
            continue
        raw_mid = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', mid_m.group(1)))
        raw_mstr = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', mstr_m.group(1)))
        if not raw_mid.strip():
            continue
        key = po_to_plain(raw_mid)
        snap = snap_zh.get(key)
        if not snap:
            continue
        snap_plain_txt = snapshot_plain(snap)

        entry_report = {"msgid": raw_mid[:80], "action": None}

        if "#, fuzzy" in block:
            # fuzzy 复核成果：若快照译文与 fuzzy 译文一致 → 摘 fuzzy 保留译文
            if snapshot_plain(snap) == po_to_plain(raw_mstr).strip():
                block = block.replace("\n#, fuzzy", "").replace("#, fuzzy\n", "")
                entry_report["action"] = "fuzzy-reviewed"
                fuzzy_fixed += 1
            else:
                # fuzzy 但我们有更好的译文 → 替换并摘 fuzzy
                block = block.replace("\n#, fuzzy", "").replace("#, fuzzy\n", "")
                new_mstr = json.dumps(snap, ensure_ascii=False)
                block = re.sub(r'(msgstr ")(?:(?!"\n|").)*("?)',
                               lambda m: m.group(1) + new_mstr + m.group(2),
                               block, count=1, flags=re.S)
                entry_report["action"] = "fuzzy-revised"
                fuzzy_fixed += 1
            entry_report["zh"] = snap
            report.append(entry_report)
        elif not raw_mstr.strip():
            # 空条目：填入我们的译文
            new_mstr = json.dumps(snap, ensure_ascii=False)
            block = re.sub(r'(msgstr ")(?:(?!"\n|").)*("?)',
                           lambda m: m.group(1) + new_mstr + m.group(2),
                           block, count=1, flags=re.S)
            entry_report["action"] = "filled"
            entry_report["zh"] = snap
            report.append(entry_report)
            improved += 1
        elif po_to_plain(raw_mstr).strip() != snap_plain_txt and snapshot_plain(snap) != po_to_plain(raw_mstr).strip():
            # 两者都有译文但不同 → 记入清单供人工对照（不自动覆盖上游社区译文）
            entry_report["action"] = "differs"
            entry_report["ref_zh"] = raw_mstr
            entry_report["our_zh"] = snap
            report.append(entry_report)

    # 重拼接（block 本身就是列表元素引用，原地改写 msgstr 后顺序不变）
    out_text = "".join(blocks)

    # ---- 头部元数据更新 ----
    now = datetime.now().strftime("%Y-%m-%d %H:%M+0000")
    out_text = re.sub(
        r'"PO-Revision-Date: [^"]*"',
        f'"PO-Revision-Date: {now}"',
        out_text, count=1)

    OUT_PO.write_text(out_text, encoding="utf-8")
    OUT_REPORT.write_text(
        json.dumps({
            "generated_at": now,
            "counts": {
                "filled_empty": improved,
                "fuzzy_fixed": fuzzy_fixed,
                "differs_for_manual_review": sum(
                    1 for r in report if r["action"] == "differs"),
            },
            "entries": report,
        }, ensure_ascii=False, indent=1),
        encoding="utf-8")

    diff_n = sum(1 for r in report if r["action"] == "differs")
    print(f"贡献文件：{OUT_PO.name}")
    print(f"  填充空条目 {improved} 条；fuzzy 复核 {fuzzy_fixed} 条；")
    print(f"  与上游译文有差异供人工对照 {diff_n} 条（清单见 {OUT_REPORT.name}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
