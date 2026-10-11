#!/usr/bin/env python3
"""导出 fuzzy 复核工作清单：新英文原文 + 旧中文译文 配对。"""
import json
import re
from pathlib import Path

SRC = Path("C:/Users/tiger/Downloads/gtkmm-documentation.tutorial-doc.master.zh_CN.po")

blocks = re.split(r"\n\s*\n", SRC.read_text(encoding="utf-8"))
pairs = []
for block in blocks:
    if "#, fuzzy" not in block or "msgid" not in block:
        continue
    mid_m = re.search(r"msgid ((?:(?!\nmsgstr).|\n)+)", block)
    mstr_m = re.search(r"msgstr ((?:(?!\nmsgstr).|\n)+)", block)
    if not mid_m or not mstr_m:
        continue
    en = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', mid_m.group(1)))
    zh = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', mstr_m.group(1)))
    if en.strip():
        pairs.append({"en": en, "zh": zh})

out = Path(__file__).resolve().parent / "_fuzzy_worklist.json"
out.write_text(json.dumps(pairs, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"复核工作清单: {len(pairs)} 条 → {out.name}")
