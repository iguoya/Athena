#!/usr/bin/env python3
"""T-001 零遗漏校验：范围内每个被跟踪文件必须被 manifest 某单元负责或明确 drop。

单元→文件的映射规则与 manifest-design-patterns.json 一一对应；本脚本独立展开，
输出每单元负责文件数与未覆盖文件清单（应为空）。
"""
import fnmatch
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(".cache/legacy-src")

def tracked(repo: str, prefix: str | None) -> list[str]:
    cmd = ["git", "-C", str(ROOT / repo), "ls-files", "-z"]
    if prefix:
        cmd += ["--", prefix]
    out = subprocess.run(cmd, capture_output=True).stdout
    return [f"{repo}/{p.decode('utf-8')}" for p in out.split(b"\0") if p]

FILES = (tracked("DesignPattern", None) + tracked("DesignPatterns", None)
         + tracked("Practice", "DesignPatterns") + tracked("Linux", "DesignPattern")
         + tracked("Linux", "DesignEvolutionCpp") + tracked("algorithm", "design-patterns"))

def g(pat: str) -> list[str]:
    return fnmatch.filter(FILES, pat)

def under(dirpath: str) -> list[str]:
    d = PurePosixPath(dirpath).as_posix()
    return [f for f in FILES if f == d or f.startswith(d + "/")]

def exact(*ps: str) -> list[str]:
    return [p for p in ps if p in FILES]

# ---- 规则表：单元 -> 负责的文件；先具体后通配，先到先得 ----
RULES: list[tuple[str, list[str]]] = []

# drop-junk：CI/部署/包管理/CodeLite 工程/构建配置（顶层精确路径）
bc = exact("DesignPattern/.gitlab-ci.yml", "DesignPattern/.travis.yml",
           "DesignPattern/.readthedocs.yml", "DesignPattern/.gitignore",
           "DesignPattern/deploy.sh", "DesignPattern/book.json",
           "DesignPattern/package.json", "DesignPattern/yarn.lock",
           "DesignPattern/pyproject.toml", "DesignPattern/SUMMARY.md",
           "DesignPattern/README.md", "DesignPattern/README.en.md", "DesignPattern/README.rst",
           "DesignPattern/DesignPattern.workspace",
           "DesignPatterns/.gitlab-ci.yml", "DesignPatterns/.travis.yml",
           "DesignPatterns/.gitignore", "DesignPatterns/deploy.sh",
           "DesignPatterns/package.json", "DesignPatterns/yarn.lock",
           "DesignPatterns/DesignPattern.workspace",
           "DesignPattern/StrategyV0/Strategy.mk", "DesignPattern/StrategyV0/Strategy.project",
           "DesignPattern/StrategyV0/Strategy.txt",
           "DesignPatterns/workspace/Strategy/Strategy.mk",
           "DesignPatterns/workspace/Strategy/Strategy.project",
           "DesignPatterns/workspace/Strategy/Strategy.txt",
           "DesignPatterns/workspace/TemplateMethod/TemplateMethod.mk",
           "DesignPatterns/workspace/TemplateMethod/TemplateMethod.project",
           "DesignPatterns/workspace/TemplateMethod/TemplateMethod.txt")
bc += under("DesignPattern/docs/.vuepress") + under("DesignPatterns/docs/.vuepress")
RULES.append(("dp-arch-build-ci", sorted(set(bc))))

# drop-junk：编辑器/IDE 产物与编译二进制（精确部分；通配兜底在最后一条规则）
ide_exact = exact("DesignPattern/Untitled.mdj", "DesignPattern/DesignPattern.pro.user",
                  "DesignPattern/SimpleFactory/SimpleFactory", "DesignPattern/SimpleFactory/uml",
                  "DesignPattern/Adapter/adapter",
                  "DesignPatterns/workspace/SimpleFactory/SimpleFactory",
                  "DesignPatterns/workspace/SimpleFactory/uml",
                  "DesignPatterns/workspace/Adapter/adapter")
RULES.append(("dp-arch-ide-artifacts", sorted(ide_exact)))

# drop-third-party：sphinx-gallery 官方样板（文档系统练手时的整套样例）
sg = (under("DesignPattern/docs/SampleModule") + under("DesignPattern/docs/auto_gallery-1")
      + under("DesignPattern/docs/auto_gallery-2") + under("DesignPattern/docs/sample-gallery-1")
      + under("DesignPattern/docs/sample-gallery-2"))
RULES.append(("dp-arch-sphinx-gallery", sorted(set(sg))))

# drop-junk：Sphinx/mermaid 文档系统练习（与设计模式无关）
de = (exact("DesignPattern/docs/conf.py", "DesignPattern/docs/index.rst",
            "DesignPattern/docs/about.rst", "DesignPattern/docs/Makefile",
            "DesignPattern/docs/make.bat", "DesignPattern/docs/requirements.txt")
      + under("DesignPattern/docs/2020") + under("DesignPattern/docs/0-diagrams"))
RULES.append(("dp-arch-doc-experiments", sorted(set(de))))

# drop-third-party：李建忠《C++设计模式》网课官方配套资源包
RULES.append(("dp-arch-courseware", under("DesignPatterns/docs/W设计模式课件")))

# drop-junk：Xcode Hello World 模板壳
RULES.append(("dp-arch-xcode-shells",
              under("DesignPatterns/AAA") + under("DesignPatterns/CCC")
              + under("DesignPatterns/DesignPatterns")))

# drop-duplicate：三处镜像
RULES.append(("dp-arch-linux-mirror", under("Linux/DesignPattern")))
RULES.append(("dp-arch-practice-mirror", under("Practice/DesignPatterns")))
RULES.append(("dp-arch-workspace-mirror",
              sum((under(f"DesignPatterns/workspace/{m}") for m in
                   ["AbstractFactory", "Adapter", "Factory", "Observer", "SimpleFactory", "Singleton"]), [])))

# drop-junk 通配：编辑器自动备份/IDE 状态/编译产物（显式 drop，不随 keep 目录隐式带入）
ide_glob: list[str] = []
for pat in ["**/*.vpp.bak_*", "**/*.vpp.lck", "**/CMakeLists.txt.user*", "**/Debug/*",
            "**/Debug/**", "**/_desktop.ini", "**/*.pyc"]:
    ide_glob += g(pat)
RULES.append(("dp-arch-ide-artifacts", sorted(set(ide_glob))))

# keep：DesignPattern 仓库的模式单元
for unit, d in [("dp-arch-simple-factory", "DesignPattern/SimpleFactory"),
                ("dp-arch-factory-method", "DesignPattern/Factory"),
                ("dp-arch-abstract-factory", "DesignPattern/AbstractFactory"),
                ("dp-arch-singleton", "DesignPattern/Singleton"),
                ("dp-arch-observer", "DesignPattern/Observer"),
                ("dp-arch-adapter", "DesignPattern/Adapter"),
                ("dp-arch-facade", "DesignPattern/Facade"),
                ("dp-arch-strategy-classic", "DesignPattern/StrategyV0"),
                ("dp-arch-strategy-sort", "DesignPattern/Strategy"),
                ("dp-arch-template-method-tank", "DesignPattern/TemplateMethod"),
                ("dp-arch-state-uml", "DesignPattern/State")]:
    RULES.append((unit, under(d)))

RULES.append(("dp-arch-template-method-default",
              under("DesignPatterns/workspace/TemplateMethod")))
# strategy 经典版的重复份（与 StrategyV0 逐文件内容一致）由 classic 单元一并负责
RULES.append(("dp-arch-strategy-classic", under("DesignPatterns/workspace/Strategy")))

# keep：Qt 壳（GUI 演示器，调用 Strategy/Facade/TemplateMethod 并展示 UML svg）
qt = exact("DesignPattern/main.cpp", "DesignPattern/mainwindow.cpp", "DesignPattern/mainwindow.h",
           "DesignPattern/mainwindow.ui", "DesignPattern/resource.qrc", "DesignPattern/DesignPattern.pro",
           "DesignPattern/CMakeLists.txt", "DesignPattern/DesignPattern.mdj") + under("DesignPattern/UML")
RULES.append(("dp-arch-qt-shell", sorted(set(qt))))

# keep：笔记（algorithm 为规范版，含三篇独有；下面这些目录是重复份，只作 duplicates 标注）
notes_dup_dirs = ["DesignPattern/docs/1-design-principles", "DesignPattern/docs/1-principle",
                  "DesignPattern/docs/2-creational-patterns", "DesignPattern/docs/2-creation",
                  "DesignPattern/docs/3-architectural-patterns", "DesignPattern/docs/3-construction",
                  "DesignPattern/docs/4-behavior-patterns", "DesignPattern/docs/4-action",
                  "DesignPattern/docs/H组件协作", "DesignPatterns/docs/1-design-principles",
                  "DesignPatterns/docs/2-creational-patterns", "DesignPatterns/docs/3-architectural-patterns",
                  "DesignPatterns/docs/4-behavior-patterns", "DesignPatterns/docs/H组件协作",
                  "DesignPatterns/docs/README.md", "DesignPattern/docs/README.md"]
RULES.append(("dp-arch-notes(duplicates 标注)", sum((under(d) for d in notes_dup_dirs), [])))
RULES.append(("dp-arch-notes", under("algorithm/design-patterns")))

# keep：gtkmm 官方示例跟练改造（按 ADR 0176 对照表归 gtkmm-lab）
RULES.append(("dp-arch-gtkmm-evolution", under("Linux/DesignEvolutionCpp")))


# ---- 展开优先级：先到先得，统计与校验 ----
owner: dict[str, str] = {}
for unit, flist in RULES:
    for f in flist:
        owner.setdefault(f, unit)

missing = [f for f in FILES if f not in owner]
print(f"# 范围内被跟踪文件总数：{len(FILES)}")
print(f"# 单元负责文件统计：")
counts: dict[str, int] = {}
for f, u in owner.items():
    counts[u] = counts.get(u, 0) + 1
for unit, _flist in RULES:
    print(f"  {counts.get(unit, 0):4d}  {unit}")
print(f"# 未覆盖文件：{len(missing)}")
for f in sorted(missing):
    print("  MISS " + f)
sys.exit(1 if missing else 0)
