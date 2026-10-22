#!/usr/bin/env python3
"""T-002 零遗漏校验：数据结构与算法两领域，931 个被跟踪文件（902 + T-001 转来的 algorithm/docs 29）。

规则先具体后通配，先到先得；输出 verify-data-structures.txt 与 verify-algorithms.txt。
"""
import fnmatch
import subprocess
import sys
from pathlib import PurePosixPath

ROOT = ".cache/legacy-src"

def tracked(repo, prefix=None):
    cmd = ["git", "-C", f"{ROOT}/{repo}", "ls-files", "-z"]
    if prefix:
        cmd += ["--", prefix]
    out = subprocess.run(cmd, capture_output=True).stdout
    return [f"{repo}/{p.decode('utf-8')}" for p in out.split(b"\0") if p]

FILES = (tracked("algorithm") + tracked("Practice", "DataStructure") + tracked("Linux", "Algorithm"))
FILES = [f for f in FILES if not (f.startswith("algorithm/design-patterns/"))]  # docs 转入、design-patterns 归 T-001

def under(d):
    d = PurePosixPath(d).as_posix()
    return [f for f in FILES if f == d or f.startswith(d + "/")]

def exact(*ps):
    return [p for p in ps if p in FILES]

def g(pat):
    return fnmatch.filter(FILES, pat)

DS_RULES = [
    ("ds-arch-cpp-linear", under("algorithm/DataStructure/linear")),
    ("ds-arch-cpp-search", under("algorithm/DataStructure/search")),
    ("ds-arch-cpp-sort", under("algorithm/DataStructure/sort")),
    ("ds-arch-cpp-tree", under("algorithm/DataStructure/tree")),
    ("ds-arch-c-linear", under("algorithm/11-linner")),
    ("ds-arch-c-tree", under("algorithm/12-tree")),
    ("ds-arch-notes", under("algorithm/docs/10-数据结构总纲") + under("algorithm/docs/11-线性表")
     + under("algorithm/docs/13-树") + under("algorithm/docs/15-排序算法")
     + exact("algorithm/docs/README.md", "algorithm/DataStructure/README.md")),
    ("ds-mirror-practice", under("Practice/DataStructure")),
    ("ds-mirror-linux", under("Linux/Algorithm/DataStructure")),
]
ALGO_RULES = [
    ("algo-arch-recursion", under("algorithm/22-recursion")),
    ("algo-arch-divide", under("algorithm/23-divide_and_conconquer")),
    ("algo-arch-backtrack", under("algorithm/backtracking")),
    ("algo-arch-dict", under("algorithm/1-速学速用大辞典")),
    ("algo-arch-cpp-recursion", under("algorithm/DataStructure/recursion")),
    ("algo-arch-basic-c", under("algorithm/21-basic")),
    ("algo-arch-qt-console", under("Linux/Algorithm/Abstract") + under("Linux/Algorithm/Recursion")
     + under("Linux/Algorithm/DivideConquer") + under("Linux/Algorithm/Exhaustion")
     + under("Linux/Algorithm/Deduction") + under("Linux/Algorithm/images")
     + exact("Linux/Algorithm/main.cpp", "Linux/Algorithm/mainwindow.cpp", "Linux/Algorithm/mainwindow.h",
             "Linux/Algorithm/mainwindow.ui", "Linux/Algorithm/resource.qrc", "Linux/Algorithm/style.css",
             "Linux/Algorithm/Algorithm_zh_CN.ts", "Linux/Algorithm/CMakeLists.txt")),
    ("algo-arch-notes", under("algorithm/docs/1-算法常识") + under("algorithm/docs/2-减治法")
     + under("algorithm/docs/3-分治法") + under("algorithm/docs/4-贪婪法") + under("algorithm/docs/5-回溯法")
     + under("algorithm/docs/6-枚举法") + under("algorithm/docs/9-动态规划")),
    ("algo-mirror-linux", under("Linux/Algorithm/21-basic") + under("Linux/Algorithm/22-recursion")
     + under("Linux/Algorithm/23-divide_and_conconquer") + under("Linux/Algorithm/Backtrack")
     + under("Linux/Algorithm/1-速学速用大辞典")),
    ("algo-arch-qdarkstyle", under("Linux/Algorithm/qdarkstyle")),
    ("algo-arch-junk", exact("algorithm/README.md", "algorithm/package.json", "algorithm/yarn.lock",
                             "algorithm/.travis.yml", "algorithm/5-LineChart.md", "Linux/Algorithm/Algorithm")
     + under("algorithm/markdown") + under("algorithm/vuepress") + under("algorithm/docs/.vuepress")
     + under("Linux/Algorithm/.cmake")),
]
JUNK_GLOB = ["**/.gitignore", "**/CMakeLists.txt.user*", "**/cmake_install.cmake"]

def run(rules, title, out_path, owner):
    from pathlib import Path
    lines = [f"# {title}", "# 单元负责文件统计（junk-glob 类按最具体单元先认领）："]
    for unit, _ in rules:
        n = sum(1 for u in owner.values() if u == unit)
        print(f"{n:5d}  {unit}")
        lines.append(f"  {n:5d}  {unit}")
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


globbed = []
for pat in JUNK_GLOB:
    globbed += g(pat)
ALL = list(DS_RULES) + list(ALGO_RULES) + [("algo-arch-junk-ide", sorted(set(globbed)))]
owner = {}
for unit, flist in ALL:
    for f in flist:
        owner.setdefault(f, unit)
missing = [f for f in FILES if f not in owner]
run(DS_RULES, "data-structures 单元负责统计", "comms/legacy-archive/artifacts/zcode/verify-data-structures.txt", owner)
run(ALGO_RULES, "algorithms 单元负责统计", "comms/legacy-archive/artifacts/zcode/verify-algorithms.txt", owner)
print(f"总文件 {len(FILES)}，合并覆盖 {len(owner)}，未覆盖 {len(missing)}")
for f in missing:
    print("  MISS", f)
sys.exit(1 if missing else 0)
