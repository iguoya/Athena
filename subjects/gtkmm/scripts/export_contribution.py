#!/usr/bin/env python3
"""从快照反向生成标准 po 贡献文件：反哺上游 / Damned Lies 的产出工具。

做法：以基准 po（po/reference.zh_CN.po，官方模板的最新翻译状态）为骨架——
msgid/位置/注释全部保留原样——只把「我们有更好译文」的条目替换 msgstr：

- 覆盖改进：基准里空或 fuzzy 的条目，若快照指纹命中则填入我们的译文（并摘除 fuzzy）；
- 质量修订：基准已有译文但与快照译文不同 → 默认保留基准（尊重上游社区译文），
  我们的译文写入随附的「贡献清单」供人工对照，人工确认更优的可手工替换。

译文输入源（应用 ADR 0004、0005）：
- 单元级（主）：content/po-units/ 的对齐映射（scripts/align_po.py 生成）把
  PO 翻译单元对应到快照连续段落——指纹 = 各段指纹拼接，与 msgid 精确匹配；
  我们的译文取应用内自译草稿（progress/learning.db 的 my_translations，
  按单元锚点 sha 存，自译优先），无自译时取各段 zh 拼接（须全段有译文，
  残缺不猜）；
- 段级（兜底）：未对齐的段按单段指纹匹配（旧口径）。
草稿永不自动成为贡献 PO 里的正式译文；与上游译文不同的进 differs 清单。

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
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_po import po_to_plain, snapshot_plain  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REF_PO = PROJECT_ROOT / "po" / "reference.zh_CN.po"
CHAPTERS = PROJECT_ROOT / "content" / "chapters"
PO_UNITS_DIR = PROJECT_ROOT / "content" / "po-units"
DB = PROJECT_ROOT / "progress" / "learning.db"
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

    # ---- 学习者自译草稿（应用 ADR 0004）：单元锚点 sha → 译文；库不存在时为空 ----
    my_zh: dict[str, str] = {}
    if DB.is_file():
        connection = sqlite3.connect(DB)
        try:
            my_zh = dict(connection.execute("SELECT sha, text FROM my_translations"))
        finally:
            connection.close()

    # ---- 快照块索引（sha → block），供单元对齐 ----
    blocks_by_sha: dict[str, dict] = {}
    for f in sorted(CHAPTERS.rglob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for block in data["blocks"]:
            if block["type"] in ("para", "listitem") and block.get("sha"):
                blocks_by_sha.setdefault(block["sha"], block)

    # ---- 快照译文集合（纯文本指纹 → 中文）----
    # 单元级优先（应用 ADR 0005）：映射把 PO 翻译单元对应到连续段落区间，
    # 指纹 = 各段指纹拼接；译文 = 自译优先，否则各段 zh 拼接（须全段有译文）。
    # 未对齐段回退段级指纹（旧口径）。先到先得：单元级先登记。
    snap_zh: dict[str, str] = {}
    snap_source: dict[str, str] = {}

    def record(key: str, zh: str, source: str) -> None:
        snap_zh.setdefault(key, zh)
        snap_source.setdefault(key, source)

    for units_path in sorted(PO_UNITS_DIR.glob("*.json")):
        pages = json.loads(units_path.read_text(encoding="utf-8"))
        for units in pages.values():
            for unit in units:
                segs = [blocks_by_sha.get(sha) for sha in unit.get("shas", [])]
                if not segs or any(s is None for s in segs):
                    continue
                mine = my_zh.get(unit.get("id") or "")
                if mine:
                    zh, source = mine, "self-translation"
                else:
                    zhs = [s.get("zh") for s in segs]
                    if not all(zhs):
                        continue  # 单元有段缺译文：残缺不猜，留待译流程
                    zh, source = " ".join(zhs), "snapshot"
                record(
                    " ".join(snapshot_plain(s["text"]) for s in segs),
                    zh,
                    source,
                )

    for f in sorted(CHAPTERS.rglob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for block in data["blocks"]:
            if block["type"] not in ("para", "listitem"):
                continue
            key = snapshot_plain(block["text"])
            mine = my_zh.get(block.get("sha") or "")
            zh = mine or block.get("zh")
            if zh:
                record(key, zh, "self-translation" if mine else "snapshot")

    # ---- 行级解析 ref po 并按条目改写 msgstr ----
    # 旧实现用正则从块里提取 msgid：\n 交替分支绕过负前瞻，msgid 会把
    # msgstr 内容一并吞进去——所有非空条目的指纹全错，differs/fuzzy
    # 通道从未生效过。改为行级状态机（与 parse_po 同口径），msgid 即 msgid。
    lines = ref_text.splitlines()
    improved = fuzzy_fixed = 0
    report: list[dict] = []
    drop: set[int] = set()  # 待删除的行号：摘除的 #, fuzzy 行、被重写的 msgstr 续行

    def po_quote(text: str) -> str:
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'

    def read_field(prefix: str, i: int) -> tuple[str, int]:
        first = lines[i][len(prefix):]
        if first.endswith('"'):
            first = first[:-1]
        parts = [first]
        j = i + 1
        while j < len(lines) and lines[j].startswith('"'):
            cont = lines[j]
            parts.append(cont[1:-1] if cont.endswith('"') else cont[1:])
            j += 1
        return "".join(parts), j

    i = 0
    while i < len(lines):
        if not lines[i].startswith('msgid "'):
            i += 1
            continue
        raw_mid, j = read_field('msgid "', i)
        raw_mstr = ""
        mstr_at = None
        mstr_end = j
        if j < len(lines) and lines[j].startswith('msgstr "'):
            raw_mstr, mstr_end = read_field('msgstr "', j)
            mstr_at = j
            j = mstr_end
        if not raw_mid.strip():
            i = j
            continue
        key = po_to_plain(raw_mid)
        snap = snap_zh.get(key)
        if not snap:
            i = j
            continue
        snap_plain_txt = snapshot_plain(snap)
        source = snap_source.get(key, "snapshot")

        # 条目头注释（上方连续 # 行）里是否标了 fuzzy；摘除时保留同行其他标志
        # （上游可能写 `#, fuzzy, no-wrap`，整行删会误伤）
        s = i - 1
        fuzzy_at = None
        while s >= 0 and lines[s].startswith("#"):
            if lines[s].startswith("#,") and "fuzzy" in lines[s]:
                fuzzy_at = s
            s -= 1

        def strip_fuzzy_flag(line: str) -> str:
            flags = [f.strip() for f in line[2:].split(",") if f.strip() and f.strip() != "fuzzy"]
            return "#, " + ", ".join(flags) if flags else ""

        def replace_msgstr(new_zh: str) -> None:
            lines[mstr_at] = "msgstr " + po_quote(new_zh)
            for k in range(mstr_at + 1, mstr_end):
                drop.add(k)  # 旧多行译文的续行一并丢弃

        entry_report = {"msgid": raw_mid[:80], "action": None, "source": source}
        if fuzzy_at is not None:
            if stripped := strip_fuzzy_flag(lines[fuzzy_at]):
                lines[fuzzy_at] = stripped  # 保留其余标志
            else:
                drop.add(fuzzy_at)
            if snapshot_plain(snap) == po_to_plain(raw_mstr).strip():
                # fuzzy 复核成果：快照译文与 fuzzy 译文一致 → 摘 fuzzy 保留译文
                entry_report["action"] = "fuzzy-reviewed"
            else:
                # fuzzy 但我们有更好的译文 → 替换并摘 fuzzy
                replace_msgstr(snap)
                entry_report["action"] = "fuzzy-revised"
                entry_report["zh"] = snap
            fuzzy_fixed += 1
            report.append(entry_report)
        elif not raw_mstr.strip():
            # 空条目：填入我们的译文
            replace_msgstr(snap)
            entry_report["action"] = "filled"
            entry_report["zh"] = snap
            report.append(entry_report)
            improved += 1
        elif (
            mstr_at is not None
            and po_to_plain(raw_mstr).strip() != snap_plain_txt
            and snapshot_plain(snap) != po_to_plain(raw_mstr).strip()
        ):
            # 两者都有译文但不同 → 记入清单供人工对照（不自动覆盖上游社区译文）
            entry_report["action"] = "differs"
            entry_report["ref_zh"] = raw_mstr
            entry_report["our_zh"] = snap
            report.append(entry_report)
        i = j

    out_text = "\n".join(line for idx, line in enumerate(lines) if idx not in drop) + "\n"

    # ---- 头部元数据更新：修订时间、贡献者署名与复数规则 ----
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M%z")
    out_text = re.sub(
        r'"PO-Revision-Date: [^"]*"',
        f'"PO-Revision-Date: {now}"',
        out_text, count=1)
    out_text = re.sub(
        r'"Last-Translator: [^"]*"',
        '"Last-Translator: tiger <375478250@qq.com>"',
        out_text, count=1)
    if '"Plural-Forms:' not in out_text:
        # zh_CN 无复数变化；Damned Lies 的合规检查期望这个头部
        out_text = out_text.replace(
            '"Content-Transfer-Encoding: 8bit\\n"',
            '"Content-Transfer-Encoding: 8bit\\n"\n"Plural-Forms: nplurals=1; plural=0;\\n"',
            1)

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
