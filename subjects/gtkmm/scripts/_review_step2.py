#!/usr/bin/env python3
"""fuzzy 复核·第二步：应用决策（机械批）+ 导出正文第一批。"""
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent

# ---- 1) 机械批决策应用：全部去 fuzzy 保留旧译 ----
cls = json.loads((WORK / "_fuzzy_classify.json").read_text(encoding="utf-8"))
pairs = json.loads((WORK / "_fuzzy_worklist.json").read_text(encoding="utf-8"))
decisions = {}
for idx in cls["names"] + cls["gfdl"]:
    decisions[str(idx)] = {"action": "keep"}
(WORK / "_decisions_batch0.json").write_text(
    json.dumps(decisions, ensure_ascii=False), encoding="utf-8")
print(f"机械批决策 {len(decisions)} 条（keep：复核通过保留旧译）")

# ---- 2) 正文第一批导出（120 条）----
body = cls["body"]
batch = body[:120]
out = [
    {"idx": i, "en": pairs[i]["en"], "zh": pairs[i]["zh"]}
    for i in batch
]
(WORK / "_body_batch1.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"正文第一批 {len(out)} 条 → _body_batch1.json（剩余 {len(body) - len(out)} 条后续批次）")
