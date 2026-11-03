"""河南：使用者 2026-11-03 指出——计算机科学与技术（080901）、软件工程（080902）在专业一览表里的「被合并专业不接受新生报考」只是旧专业代码并入新代码、主考院校归并，
专业本身没有停考。把 082208、080720 两条 stopped 记录并进同专业的开考记录（local_code 写全，备注说明代码合并），不再有「停考」记录。
用法：python -X utf8 build_henan_merge_fix.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "tools"))
import provlib  # noqa: E402

provlib.DATE = "2026-11-03"
from provlib import *  # noqa: E402,F403

MERGE = {"080901": ("080702", "082208"), "080902": ("080711", "080720")}
p = CONTENT / "provinces" / "henan.json"
d = provlib._load(p)
out = []
for o in d["offerings"]:
    m = o["major"]
    if m in MERGE:
        keep, merged = MERGE[m]
        if o.get("local_code") == merged:
            continue
        if o.get("local_code") == keep:
            o["local_code"] = f"{keep}、{merged}"
            o["matched_by"] = f"一览表新专业代码 {m} 对应原专业代码 {keep}、{merged}（均为{ '计算机科学与技术' if m == '080901' else '软件工程' }，两个旧代码并入新代码）"
            o["status"] = "open"
            o["verify"]["note"] = (o["verify"]["note"].split("；备注：")[0]
                                   + f"；一览表备注「被合并专业不接受新生报考」指旧代码 {merged} 并入新代码 {m}，专业本身没有停考，主考院校为河南科技大学（使用者 2026-11-03 指正）")
    out.append(o)
d["offerings"] = out
provlib._save(p, d)
print("henan merge ok", [(o["major"], o["local_code"], o["status"]) for o in out if o["status"] != "none"])
