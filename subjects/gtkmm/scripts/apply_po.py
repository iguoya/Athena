#!/usr/bin/env python3
"""官方译文优先：把 zh_CN.po 的现有翻译按段落指纹对齐填充到快照。

翻译优先级（应用 ADR 0002 的补充约定）：
  1. 官方 po 现有译文（本脚本）——信达雅以社区审定为准；
  2. 官方仓库历史翻译（git log 老版本 po，后续需要时再加 --history）；
  3. 自行翻译（工具辅助 + 人工校订），只处理前两级都找不到的段。

只填充 zh 为空的文字段；已有译文不覆盖。--apply 才写盘，默认预览。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_source import expand_entities  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PO = (PROJECT_ROOT / "upstream" / "gtkmm-documentation" / "docs" / "tutorial"
      / "zh_CN" / "zh_CN.po")
CHAPTERS = PROJECT_ROOT / "content" / "chapters"


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def parse_po(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith('msgid "'):
            def read_field(start: int, prefix: str) -> tuple[str, int]:
                first = lines[start][len(prefix):]
                parts = [first[:-1] if first.endswith('"') else first]
                j = start + 1
                while j < len(lines) and lines[j].startswith('"'):
                    s = lines[j]
                    parts.append(s[1:-1] if s.endswith('"') else s[1:])
                    j += 1
                return "".join(parts), j
            msgid, i = read_field(i, 'msgid "')
            msgstr, i = (read_field(i, 'msgstr "') if i < len(lines)
                         and lines[i].startswith('msgstr "') else ("", i))
            entries[msgid] = msgstr
        else:
            i += 1
    return entries


def po_to_plain(raw: str) -> str:
    """po 的 msgid（含 DocBook 标签）→ 与快照指纹同口径的纯文本。"""
    text = expand_entities(raw)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def snapshot_plain(text: str) -> str:
    """快照段落（内联 markdown）→ 纯文本指纹口径。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    force_utf8()
    apply = "--apply" in sys.argv
    po_entries = parse_po(PO.read_text(encoding="utf-8"))
    # 纯文本 → 译文（po 的 msgstr 同样转纯文本；多个 msgid 归一后撞键时先到先得）
    plain_zh: dict[str, str] = {}
    for msgid, msgstr in po_entries.items():
        if not msgstr.strip():
            continue
        key = po_to_plain(msgid)
        plain_zh.setdefault(key, po_to_plain(msgstr))

    filled = skipped_existing = not_found = 0
    for path in sorted(CHAPTERS.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for block in data["blocks"]:
            if block["type"] not in ("para", "listitem") or block.get("zh"):
                continue
            key = snapshot_plain(block["text"])
            zh = plain_zh.get(key)
            if zh:
                block["zh"] = zh
                block.pop("status", None)
                block.pop("stale_from", None)
                filled += 1
                changed = True
            else:
                not_found += 1
        if changed and apply:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    verb = "已填充" if apply else "可填充（--apply 生效）"
    print(f"官方 po 对齐：{verb} {filled} 段；po 中无对应译文 {not_found} 段（留给自译流程）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
