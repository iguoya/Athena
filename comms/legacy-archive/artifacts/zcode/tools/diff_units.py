# -*- coding: utf-8 -*-
"""对同名但内容不同的候选单元做文件级对齐，输出差异报告。"""
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(r"C:\Users\tiger\Athena\comms\legacy-archive\artifacts\zcode")
records = json.loads((BASE / "scan.json").read_text(encoding="utf-8"))

PAIRS = [
    ("11-linner", "algorithm", "11-linner/", "Linux", "Algorithm/DataStructure/11-linner/"),
    ("12-tree", "algorithm", "12-tree/", "Linux", "Algorithm/DataStructure/12-tree/"),
    ("dacidian", "algorithm", "1-速学速用大辞典/", "Linux", "Algorithm/1-速学速用大辞典/"),
    ("dp-docs", "DesignPattern", "docs/", "Linux", "DesignPattern/docs/"),
    ("21-basic", "algorithm", "21-basic/", "Linux", "Algorithm/21-basic/"),
    ("Strategy", "DesignPattern", "Strategy/", "DesignPatterns", "workspace/Strategy/"),
    ("TemplateMethod", "DesignPattern", "TemplateMethod/", "DesignPatterns", "workspace/TemplateMethod/"),
]

by_repo = defaultdict(dict)
for r in records:
    by_repo[r["repo"]][r["path"]] = r

for name, ra, pa, rb, pb in PAIRS:
    A = {p[len(pa):]: r for p, r in by_repo[ra].items() if p.startswith(pa)}
    B = {p[len(pb):]: r for p, r in by_repo[rb].items() if p.startswith(pb)}
    same = [k for k in A.keys() & B.keys() if A[k]["norm"] == B[k]["norm"]]
    diff = [k for k in A.keys() & B.keys() if A[k]["norm"] != B[k]["norm"]]
    only_a = sorted(A.keys() - B.keys())
    only_b = sorted(B.keys() - A.keys())
    print(f"\n===== {name}: {ra}/{pa} ({len(A)}) vs {rb}/{pb} ({len(B)})")
    print(f"同名同内容 {len(same)}，同名异内容 {len(diff)}，仅A {len(only_a)}，仅B {len(only_b)}")
    for k in diff[:10]:
        print(f"  [异] {k}: A {A[k]['size']}B  B {B[k]['size']}B")
    for k in only_a[:15]:
        print(f"  [仅{ra}] {k} ({A[k]['size']}B)")
    for k in only_b[:15]:
        print(f"  [仅{rb}] {k} ({B[k]['size']}B)")

# dp:docs 内部重复检查：DesignPattern/docs 96 文件只有 78 种内容
print("\n===== DesignPattern/docs 内部重复（规范化哈希相同的文件对）")
docs = [r for r in records if r["repo"] == "DesignPattern" and r["path"].startswith("docs/")]
h = defaultdict(list)
for r in docs:
    h[r["norm"]].append(r["path"])
for norm, paths in h.items():
    if len(paths) > 1:
        print("  " + " | ".join(paths))
