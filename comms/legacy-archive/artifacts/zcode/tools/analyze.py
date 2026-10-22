# -*- coding: utf-8 -*-
"""按规范化单元名聚合 scan.json，输出跨仓库重复矩阵，供单元划分与规范版判定。"""
import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(r"C:\Users\tiger\Athena\comms\legacy-archive\artifacts\zcode")
records = json.loads((BASE / "scan.json").read_text(encoding="utf-8"))

CODE_EXTS = {".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hh", ".py", ".qml", ".ui"}


def unit_of(repo: str, path: str) -> str:
    """把 (repo, 路径) 映射到规范化单元名。None 表示尚未归属。"""
    p = path
    if repo == "DesignPattern":
        return "dp:" + p.split("/")[0]
    if repo == "DesignPatterns":
        if p.startswith("workspace/"):
            return "dp:" + p.split("/")[1]
        if p.startswith(("AAA/", "CCC/", "DesignPatterns/")):
            return "dp:xcode-shells"
        if p.startswith("docs/"):
            return "dp:DesignPatterns-docs"
        return "dp:DesignPatterns-misc"
    if repo == "Practice":
        if p.startswith("DesignPatterns/"):
            return "dp:" + p.split("/")[1]
        if p.startswith("DataStructure/"):
            rest = p[len("DataStructure/"):]
            return "ds:" + (rest.split("/")[0] if "/" in rest else "readme")
    if repo == "Linux":
        if p.startswith("DesignPattern/"):
            return "dp:" + p[len("DesignPattern/"):].split("/")[0]
        if p.startswith("DesignEvolutionCpp/"):
            return "dp:DesignEvolutionCpp"
        if p.startswith("Algorithm/"):
            rest = p[len("Algorithm/"):]
            top = rest.split("/")[0]
            if top == "qdarkstyle":
                return "alg:qdarkstyle"
            if top == "DataStructure":
                sub = rest.split("/")[1] if "/" in rest else "readme"
                return "ds:" + sub
            return "alg:" + top
        if p.startswith("C/"):
            return "c-lang:" + p.split("/")[1]
    if repo == "algorithm":
        if p.startswith("design-patterns"):
            return "dp:algorithm-notes"
        top = p.split("/")[0]
        if top in ("DataStructure",):
            rest = p[len("DataStructure/"):]
            return "ds:" + (rest.split("/")[0] if "/" in rest else "readme")
        if top in ("11-linner", "12-tree", "21-basic", "22-recursion",
                   "23-divide_and_conconquer", "backtracking"):
            return "alg:" + top
        if top.startswith("1-速学速用大辞典"):
            return "alg:dacidian"
        return "alg:site-" + top.rstrip('"')
    return "unassigned"


def canon(u: str) -> str:
    """把单元名里的模式名归一（大小写无关紧要，名字完全一致的才合并）。"""
    return u


by_unit = defaultdict(list)
for r in records:
    by_unit[canon(unit_of(r["repo"], r["path"]))].append(r)

# 对每个规范化单元，按 repo 列出文件数与哈希集合
groups = defaultdict(lambda: defaultdict(list))  # unit -> repo -> records
for u, rs in by_unit.items():
    for r in rs:
        groups[u][r["repo"]].append(r)

for u in sorted(groups):
    repos = groups[u]
    total = sum(len(v) for v in repos.values())
    if total <= 1:
        continue
    print(f"\n== {u}  (共 {total}) ==")
    hash_repo = defaultdict(set)
    for repo, rs in repos.items():
        print(f"  {repo}: {len(rs)} 文件")
        for r in rs:
            hash_repo[r["norm"]].add(repo)
    # 有多少规范化内容出现在两个以上 repo
    dup = {h: rs for h, rs in hash_repo.items() if len(rs) > 1}
    uniq = len(hash_repo)
    print(f"  规范化内容种类 {uniq}，其中跨 repo 重复 {len(dup)}")
