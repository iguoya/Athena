# -*- coding: utf-8 -*-
"""对候选规范版路径批量取 git 首次/最后提交日期。"""
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\tiger\Athena\.cache\legacy-src")

# (repo, path)
TARGETS = [
    # 设计模式：四处重复的模式，查四个仓库的首次提交
    *[(r, f"{d}/") for r, d in [
        ("DesignPattern", "Adapter"), ("DesignPatterns", "workspace/Adapter"), ("Practice", "DesignPatterns/Adapter"), ("Linux", "DesignPattern/Adapter"),
        ("DesignPattern", "SimpleFactory"), ("DesignPatterns", "workspace/SimpleFactory"), ("Practice", "DesignPatterns/SimpleFactory"),
        ("DesignPattern", "Observer"), ("DesignPatterns", "workspace/Observer"), ("Practice", "DesignPatterns/Observer"),
        ("DesignPattern", "Factory"), ("DesignPatterns", "workspace/Factory"), ("Practice", "DesignPatterns/Factory"),
        ("DesignPattern", "AbstractFactory"), ("DesignPatterns", "workspace/AbstractFactory"), ("Practice", "DesignPatterns/AbstractFactory"),
        ("DesignPattern", "Singleton"), ("DesignPatterns", "workspace/Singleton"), ("Practice", "DesignPatterns/Singleton"),
        ("DesignPattern", "Strategy"), ("DesignPatterns", "workspace/Strategy"),
        ("DesignPattern", "StrategyV0"),
        ("DesignPattern", "TemplateMethod"), ("DesignPatterns", "workspace/TemplateMethod"),
        ("DesignPattern", "Facade"), ("DesignPattern", "State"),
        ("DesignPattern", "docs"), ("DesignPatterns", "docs"),
        ("DesignPattern", "UML"),
        ("DesignPatterns", "AAA"), ("DesignPatterns", "CCC"), ("DesignPatterns", "DesignPatterns"),
        ("algorithm", "design-patterns"),
        ("Linux", "DesignEvolutionCpp"),
    ]],
    # 数据结构：三处全同的五个单元
    *[(r, f"DataStructure/{d}") for r, d in [
        ("algorithm", "DataStructure/linear"), ("Practice", "DataStructure/linear"), ("Linux", "Algorithm/DataStructure/linear"),
        ("algorithm", "DataStructure/recursion"), ("Practice", "DataStructure/recursion"),
        ("algorithm", "DataStructure/search"), ("algorithm", "DataStructure/sort"), ("algorithm", "DataStructure/tree"),
    ]],
    # 算法目录
    *[(r, p) for r, p in [
        ("algorithm", "11-linner"), ("Linux", "Algorithm/DataStructure/11-linner"),
        ("algorithm", "12-tree"), ("Linux", "Algorithm/DataStructure/12-tree"),
        ("algorithm", "21-basic"), ("Linux", "Algorithm/21-basic"),
        ("algorithm", "22-recursion"), ("Linux", "Algorithm/22-recursion"),
        ("algorithm", "23-divide_and_conconquer"), ("Linux", "Algorithm/23-divide_and_conconquer"),
        ("algorithm", "backtracking"),
        ("algorithm", "1-速学速用大辞典"), ("Linux", "Algorithm/1-速学速用大辞典"),
        ("algorithm", "markdown"), ("algorithm", "docs"), ("algorithm", "vuepress"),
        ("Linux", "Algorithm/Recursion"), ("Linux", "Algorithm/DivideConquer"),
        ("Linux", "Algorithm/Backtrack"), ("Linux", "Algorithm/Exhaustion"),
        ("Linux", "Algorithm/Deduction"), ("Linux", "Algorithm/Abstract"),
        ("Linux", "Algorithm/qdarkstyle"), ("Linux", "Algorithm/images"),
        ("Linux", "C"), ("Linux", "Algorithm/DataStructure"),
    ]],
]

print(f"{'repo':<15} {'path':<42} {'首次':<12} {'最后':<12} 提交数")
for repo, path in TARGETS:
    cwd = ROOT / repo
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "log", "--format=%ad", "--date=short", "--", path],
        cwd=cwd, capture_output=True, check=True).stdout.decode()
    dates = [d for d in out.split() if d]
    if dates:
        print(f"{repo:<15} {path:<42} {dates[-1]:<12} {dates[0]:<12} {len(dates)}")
    else:
        print(f"{repo:<15} {path:<42} {'(无历史)':<12}")
