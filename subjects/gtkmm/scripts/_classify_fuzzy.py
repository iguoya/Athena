#!/usr/bin/env python3
"""fuzzy 复核·第一步：分类（人名/GFDL/正文）+ 机械批处理。"""
import json
import re
from pathlib import Path

SRC = Path("C:/Users/tiger/Downloads/gtkmm-documentation.tutorial-doc.master.zh_CN.po")
WORK = Path(__file__).resolve().parent / "_fuzzy_worklist.json"

pairs = json.loads(WORK.read_text(encoding="utf-8"))

names = []      # 贡献者人名条：msgstr := msgid 原样（人名不译，贡献短语含中文的保留）
gfdl = []       # GFDL 法律文本：保留旧译
body = []       # 正文：需逐条复核

for idx, p in enumerate(pairs):
    en = p["en"]
    if "<firstname>" in en and "<surname>" in en:
        names.append(idx)
    elif "Permission is granted to copy" in en or "GNU Free Documentation License" in en:
        gfdl.append(idx)
    else:
        body.append(idx)

Path(__file__).resolve().parent.joinpath("_fuzzy_classify.json").write_text(
    json.dumps({"names": names, "gfdl": gfdl, "body": body}, ensure_ascii=False),
    encoding="utf-8")
print(f"人名机械批 {len(names)} 条；GFDL {len(gfdl)} 条；正文待复核 {len(body)} 条")
