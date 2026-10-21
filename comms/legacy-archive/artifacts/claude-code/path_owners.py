#!/usr/bin/env python3
"""六个旧仓库的路径归属表：每个被跟踪文件恰好归一个任务（T-001/T-002/T-101/T-102/T-901）。
最长前缀优先；同前缀以下表为准。输出 path-owners.txt（前缀表）与校验结果。"""
import subprocess, sys, collections
from pathlib import Path

SRC = Path(__file__).resolve().parents[4] / ".cache" / "legacy-src"
REPOS = ["Practice", "Linux", "algorithm", "DesignPatterns", "DesignPattern", "Qt5"]

# (前缀, 任务)。"仓库/" 结尾表示该仓库其余全部。
TABLE = [
    # 设计模式 → T-001（含 DesignPattern 仓库根上的 Qt 壳、UML、docs 等一切）
    ("DesignPattern/", "T-001"), ("DesignPatterns/", "T-001"),
    ("Practice/DesignPatterns/", "T-001"), ("Linux/DesignPattern/", "T-001"),
    ("Linux/DesignEvolutionCpp/", "T-001"), ("algorithm/design-patterns/", "T-001"),
    ("algorithm/docs/", "T-001"),  # 先按设计模式文档处理，T-001 若发现是算法文档可在 md 里转交 T-002
    # 数据结构与算法 → T-002
    ("algorithm/", "T-002"), ("Practice/DataStructure/", "T-002"), ("Linux/Algorithm/", "T-002"),
    # Qt → T-101
    ("Qt5/", "T-101"), ("Linux/QT/", "T-101"), ("Linux/PyQt/", "T-101"), ("Linux/QML/", "T-101"),
    ("Linux/Sample/", "T-101"), ("Practice/QT/", "T-101"), ("Practice/XNode/", "T-101"),
    ("Practice/untitled/", "T-101"),
    # GTK / gtkmm → T-102
    ("Linux/GTK/", "T-102"), ("Linux/GTKMM/", "T-102"), ("Linux/Examples_Gtkmm/", "T-102"),
    ("Linux/gtkmm-application-template/", "T-102"),
    # 其余 → T-901（leader）
    ("Linux/", "T-901"), ("Practice/", "T-901"),
]
TABLE.sort(key=lambda t: -len(t[0]))

def owner(path):
    for pre, t in TABLE:
        if path.startswith(pre):
            return t
    return None

def all_files(repo):
    out = subprocess.run(["git", "-C", str(SRC / repo), "ls-files", "-z"], capture_output=True).stdout.split(b"\0")
    return [f.decode("utf-8", "replace") for f in out if f]


def main():
    cnt = collections.Counter(); unowned = []; per = collections.defaultdict(collections.Counter)
    for r in REPOS:
        out = subprocess.run(["git", "-C", str(SRC / r), "ls-files", "-z"], capture_output=True).stdout.split(b"\0")
        for f in out:
            if not f: continue
            p = f"{r}/{f.decode('utf-8','replace')}"
            t = owner(p)
            if t is None: unowned.append(p)
            else: cnt[t] += 1; per[t][r] += 1
    lines = ["# 路径归属表（最长前缀优先）。每个被跟踪文件恰好归一个任务。", ""]
    lines += [f"{t}\t{pre}" for pre, t in sorted(TABLE, key=lambda x: (x[1], x[0]))]
    lines += ["", "# 文件数统计"]
    for t in sorted(cnt): lines.append(f"{t}\t{cnt[t]}\t" + ", ".join(f"{r}:{n}" for r, n in sorted(per[t].items())))
    lines.append(f"未归属\t{len(unowned)}")
    Path(__file__).with_name("path-owners.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-8:]))
    return 1 if unowned else 0
if __name__ == "__main__":
    sys.exit(main())
