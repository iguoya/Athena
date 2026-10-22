# -*- coding: utf-8 -*-
"""T-103：从 .cache/legacy-src 拷贝原样案例到 staging/qt/content/。
只写暂存目录；不改 legacy-src。可重复运行（先清 cases 再拷）。
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]  # Athena root (artifacts/cursor/staging -> 5 up? )
# __file__ = .../comms/legacy-archive/artifacts/cursor/staging/_build_qt_staging.py
# parents: 0=staging, 1=cursor, 2=artifacts, 3=legacy-archive, 4=comms, 5=Athena
REPO = Path(__file__).resolve().parents[5]
SRC = REPO / ".cache" / "legacy-src"
STAGING = Path(__file__).resolve().parent / "qt" / "content"
CASES = STAGING / "cases"
MANIFEST = REPO / "comms" / "legacy-archive" / "artifacts" / "cursor" / "manifest-qt.json"

SKIP_SUFFIXES = (
    ".user",
    ".depend",
    ".layout",
    ".o",
    ".obj",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".a",
    ".lib",
    ".pch",
    ".pdb",
    ".ilk",
    ".exp",
)
SKIP_NAME_PARTS = (".pro.user", ".user.", ".vpp", ".lck", ".bak", ".mdj", ".workspace")
SKIP_DIRS = {
    "build",
    "debug",
    "release",
    "Debug",
    "Release",
    ".git",
    "CMakeFiles",
    "__pycache__",
    ".qmlcache",
}
MAX_BYTES = 256 * 1024

# unit -> (slug, topic_group, title_zh, difficulty)
# topic_group 用于 guide_line 前缀与排序
KEEP: dict[str, tuple[str, str, str, int]] = {
    # signals-slots
    "qt5-01-signalslot": ("signalslot", "signals-slots", "信号与槽（旧式 SIGNAL/SLOT 宏）", 2),
    "qt5-20-signalandslot": ("signalandslot", "signals-slots", "信号与槽（自定义信号跨窗口）", 3),
    # layout
    "qt5-20-layout": ("layout", "layout", "QBoxLayout 基础布局", 2),
    "qt5-24-layoutgrid": ("layoutgrid", "layout", "QGridLayout 网格布局", 2),
    "qt5-27-layoutstack": ("layoutstack", "layout", "QStackedLayout 堆叠布局", 2),
    "qt5-31-splitter": ("splitter", "layout", "QSplitter 分割条", 2),
    "qt5-60-stackwidget": ("stackwidget", "layout", "QStackedWidget 多页切换", 3),
    # windows-dialogs
    "qt5-2-muitiwindow": ("muitiwindow", "windows-dialogs", "多窗口切换（拼写 Muiti）", 2),
    "qt5-21-twowindow": ("twowindow", "windows-dialogs", "两窗口信号通信", 3),
    "qt5-3-login": ("login", "windows-dialogs", "登录对话框", 2),
    "qt5-13-embedwidget": ("embedwidget", "windows-dialogs", "嵌入子控件与布局", 3),
    "qt5-40-multifile": ("multifile", "windows-dialogs", "多文件对话框", 2),
    "qt5-56-multipage": ("multipage", "windows-dialogs", "多页窗口", 2),
    "qt5-93-qsystemtray": ("qsystemtray", "windows-dialogs", "系统托盘", 3),
    "qt5-96-dropfile": ("dropfile", "windows-dialogs", "拖放打开文件", 2),
    # model-view
    "qt5-54-studentinfo": ("studentinfo", "model-view", "学生信息表（Model/View）", 3),
    "qt5-95-qprocesslist": ("qprocesslist", "model-view", "进程列表（表格模型）", 3),
    # network / process
    "qt5-51-imageprocessor": ("imageprocessor", "network", "网络图片处理", 3),
    "qt5-81-networkinformation": ("networkinformation", "network", "网络信息查询", 2),
    "qt5-94-qprocess": ("qprocess", "network", "QProcess 启动外部进程", 2),
    "prac-xnode": ("xnode", "network", "XNode 网络节点（Server/Client/Monitor）", 4),
    # charts
    "qt5-91-qtchartsbasic": ("qtchartsbasic", "charts", "Qt Charts 基础（缺模块）", 2),
    "qt5-examples-chart": ("chart", "charts", "图表示例（Qt6 API 变更）", 3),
    # designer
    "qt5-38-designer": ("designer", "designer", "Qt Designer .ui 加载", 2),
    # basics
    "qt5-4-qmenu": ("qmenu", "basics", "QMenu 菜单", 2),
    "qt5-5-texteditor": ("texteditor", "basics", "简易文本编辑器", 3),
    "qt5-17-datetime": ("datetime", "basics", "日期时间控件", 2),
    "qt5-30-cmake": ("cmake", "basics", "CMake 构建 Qt 工程", 2),
    # qml-quick
    "qt5-8-qmlsignal": ("qmlsignal", "qml-quick", "QML 信号与 C++/QML 交互", 3),
    "qt5-22-layoutarchors": ("layoutanchors", "qml-quick", "QML Anchors 定位", 2),
    "qt5-33-quickstack": ("quickstack", "qml-quick", "StackView 页面栈", 3),
    "qt5-37-quick": ("quick", "qml-quick", "Qt Quick 综合小例", 3),
    "qt5-50-quickpi": ("quickpi", "qml-quick", "Quick 画 π / 自定义绘制", 3),
    "qt5-53-canvas": ("canvas", "qml-quick", "QML Canvas 绘图", 3),
    "qt5-57-materialstyle": ("materialstyle", "qml-quick", "Material 样式", 2),
    "qt5-65-gridquick": ("gridquick", "qml-quick", "Grid 布局与 Quick Controls", 2),
    "qml-1-layout": ("qmllayout", "qml-quick", "QML Layout（Linux/QML）", 2),
    "prac-qt-qmlbook-4-1qmlsyntax": ("qmlsyntax", "qml-quick", "QML 语法跟练（有独立片段）", 2),
    "prac-qt-qmlbook-4-5positioningelements": ("qmlpositioning", "qml-quick", "QML 定位元素跟练", 2),
    # pyqt
    "pyqt-a4-signal": ("pyqtsignal", "pyqt", "PyQt 信号与槽", 2),
    "pyqt-a6-dialog": ("pyqtdialog", "pyqt", "PyQt 对话框", 3),
    # other
    "qt5-48-backend": ("backend", "other", "QML/C++ Backend 暴露", 3),
    "qt5-63-calculatorarea": ("calculatorarea", "other", "面积计算器（Widgets）", 3),
    "qt-qtapp-app": ("qtapp", "misc-app", "QtApp 宿主小应用", 3),
}

# DesignPattern 根 Qt 壳（不在 manifest 里，leader 裁决归 qt）
DP_SHELL = {
    "slug": "dpshell",
    "group": "misc-app",
    "title": "DesignPattern Qt 壳（Strategy/Facade/TemplateMethod + UML）",
    "difficulty": 3,
    "repo": "DesignPattern",
    "path": ".",
    "first_commit": None,  # filled by git
    "files": [
        "main.cpp",
        "mainwindow.cpp",
        "mainwindow.h",
        "mainwindow.ui",
        "resource.qrc",
        "DesignPattern.pro",
        "CMakeLists.txt",
        "Facade/Facade.cpp",
        "Facade/Facade.h",
        "Facade/Navigation.cpp",
        "Facade/Navigation.h",
        "Facade/Power.cpp",
        "Facade/Power.h",
        "Facade/Rocket.cpp",
        "Facade/Rocket.h",
        "Facade/SubSystemA.cpp",
        "Facade/SubSystemA.h",
        "Facade/SubSystemB.cpp",
        "Facade/SubSystemB.h",
        "Strategy/BubbleSort.cpp",
        "Strategy/BubbleSort.h",
        "Strategy/ConcreteStrategyA.cpp",
        "Strategy/ConcreteStrategyA.h",
        "Strategy/ConcreteStrategyB.cpp",
        "Strategy/ConcreteStrategyB.h",
        "Strategy/QuickSort.cpp",
        "Strategy/QuickSort.h",
        "Strategy/SortAlgorithm.cpp",
        "Strategy/SortAlgorithm.h",
        "Strategy/Strategy.cpp",
        "Strategy/Strategy.h",
        "Strategy/StrategyContext.cpp",
        "Strategy/StrategyContext.h",
        "TemplateMethod/AbstractClass.h",
        "TemplateMethod/ConcreteClassA.cpp",
        "TemplateMethod/ConcreteClassA.h",
        "TemplateMethod/ConcreteClassB.cpp",
        "TemplateMethod/ConcreteClassB.h",
        "TemplateMethod/M1A1.cpp",
        "TemplateMethod/M1A1.h",
        "TemplateMethod/T90.cpp",
        "TemplateMethod/T90.h",
        "TemplateMethod/Tank.h",
        "UML/facade.svg",
        "UML/strategy.svg",
        "UML/templatemethod.svg",
    ],
}

GROUP_ORDER = [
    "signals-slots",
    "basics",
    "layout",
    "windows-dialogs",
    "model-view",
    "network",
    "charts",
    "designer",
    "qml-quick",
    "pyqt",
    "other",
    "misc-app",
]

BUILD_CHECKED_PASS = {
    "qt5-20-layout",
    "qt5-21-layoutbinding",
    "qt5-23-layoutcolumn",
    "qt5-54-studentinfo",
    "qt5-95-qprocesslist",
    "qt5-51-imageprocessor",
    "qt5-81-networkinformation",
    "qt5-82-networkinformation",
    "qt5-38-designer",
    "qt5-01-signalslot",
    "qt5-20-signalandslot",
    "qt5-13-embedwidget",
    "qt5-2-muitiwindow",
    "qt5-21-twowindow",
    "qt5-1-hello",
    "qt5-11-helloworld",
}


def should_skip(rel: Path) -> bool:
    name = rel.name
    if name.endswith(SKIP_SUFFIXES):
        return True
    low = str(rel).replace("\\", "/")
    for part in SKIP_NAME_PARTS:
        if part in low:
            return True
    for p in rel.parts:
        if p in SKIP_DIRS:
            return True
    return False


def first_commit(repo: str, path: str) -> str:
    r = SRC / repo
    cmd = [
        "git",
        "-C",
        str(r),
        "log",
        "--follow",
        "--format=%ad",
        "--date=short",
        "--",
        path if path != "." else ".",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            return out.splitlines()[-1]
    except Exception:
        pass
    return "unknown"


def copy_tree_filtered(
    src_dir: Path, dst_dir: Path, extra_skip_dirs: set[str] | None = None
) -> list[str]:
    """Copy tracked-ish files under src_dir; return relative paths copied."""
    skip_dirs = SKIP_DIRS | (extra_skip_dirs or set())
    copied: list[str] = []
    if src_dir.is_file():
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        if src_dir.stat().st_size <= MAX_BYTES and not should_skip(Path(src_dir.name)):
            shutil.copy2(src_dir, dst_dir)
            return [dst_dir.name]
        return []
    for p in sorted(src_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src_dir)
        if any(part in skip_dirs for part in rel.parts):
            continue
        if should_skip(rel):
            continue
        if p.stat().st_size > MAX_BYTES:
            continue
        if p.suffix.lower() in {".qmlc", ".jsc", ".dll", ".so", ".dylib", ".a", ".lib", ".exe", ".pdb"}:
            continue
        dest = dst_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        copied.append(rel.as_posix())
    return copied


def list_sources(case_dir: Path) -> list[str]:
    prefer = []
    for pat in ("*.cpp", "*.c", "*.py", "*.qml", "*.h", "*.ui", "*.qrc", "*.pro", "CMakeLists.txt"):
        for p in sorted(case_dir.rglob(pat)):
            if should_skip(p.relative_to(case_dir)):
                continue
            prefer.append(p.relative_to(case_dir).as_posix())
    # toolchain: list main entry-ish files first, cap for JSON size
    mains = [s for s in prefer if Path(s).name in ("main.cpp", "main.py", "main.qml", "mainwindow.cpp")]
    rest = [s for s in prefer if s not in mains]
    ordered = mains + rest
    # keep reasonable list
    return ordered[:40]


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_unit = {x["unit"]: x for x in manifest}

    if CASES.exists():
        shutil.rmtree(CASES)
    CASES.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)

    meta = []
    for unit, (slug, group, title, diff) in KEEP.items():
        if unit not in by_unit:
            raise SystemExit(f"missing unit in manifest: {unit}")
        u = by_unit[unit]
        canon = u["canonical"][0]
        # manifest 写 Linux/QT/QtApp/app，实际文件在 Linux/QT/QtApp（无 app 子目录）
        if canon == "Linux/QT/QtApp/app":
            canon = "Linux/QT/QtApp"
        repo, _, path = canon.partition("/")
        if not path:
            path = "."
        src = SRC / repo / path
        case = f"arc_qt_{slug}"
        dst = CASES / case
        if unit == "qt-qtapp-app":
            copied = copy_tree_filtered(src, dst, extra_skip_dirs={"qdarkstyle"})
        else:
            copied = copy_tree_filtered(src, dst)
        if not copied:
            raise SystemExit(f"no files copied for {unit} from {src}")
        meta.append(
            {
                "unit": unit,
                "slug": slug,
                "group": group,
                "title": title,
                "difficulty": diff,
                "case": case,
                "repo": repo,
                "path": path,
                "first_commit": u.get("first_commit") or first_commit(repo, path),
                "duplicates": u.get("duplicates") or [],
                "sources": list_sources(dst),
                "files_copied": len(copied),
                "build_checked_pass": unit in BUILD_CHECKED_PASS,
                "quality_notes": u.get("quality_notes") or "",
            }
        )

    # DesignPattern shell
    dp_src = SRC / "DesignPattern"
    dp_case = f"arc_qt_{DP_SHELL['slug']}"
    dp_dst = CASES / dp_case
    dp_dst.mkdir(parents=True, exist_ok=True)
    for rel in DP_SHELL["files"]:
        s = dp_src / rel
        if not s.is_file():
            print("WARN missing", rel)
            continue
        if s.stat().st_size > MAX_BYTES:
            continue
        d = dp_dst / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    dp_fc = first_commit("DesignPattern", "main.cpp")
    meta.append(
        {
            "unit": "dp-qt-shell",
            "slug": DP_SHELL["slug"],
            "group": DP_SHELL["group"],
            "title": DP_SHELL["title"],
            "difficulty": DP_SHELL["difficulty"],
            "case": dp_case,
            "repo": "DesignPattern",
            "path": ".",
            "first_commit": dp_fc,
            "duplicates": [],
            "sources": list_sources(dp_dst),
            "files_copied": sum(1 for _ in dp_dst.rglob("*") if _.is_file()),
            "build_checked_pass": False,
            "quality_notes": "Qt 壳把 Strategy/Facade/TemplateMethod 跑起来并显示 UML svg",
        }
    )

    # drop-trivial for remaining keep
    dropped_lines = [
        "# Qt 历史归档 · drop-trivial（未进应用）",
        "",
        "依据 AUTHORING.md 第一节：模板/Hello World/同主题重复变体/写不出 3 条具体批注的不进。",
        "原仓库归档后仍可取回。",
        "",
    ]
    for u in manifest:
        if u.get("verdict") != "keep":
            continue
        if u["unit"] in KEEP:
            continue
        canon = u["canonical"][0]
        reason = _drop_reason(u)
        dropped_lines.append(f"- `{canon}` — {reason}")

    # also note QmlBook/Qt5书 drops that were keep in manifest
    (STAGING / "archive-dropped.md").write_text("\n".join(dropped_lines) + "\n", encoding="utf-8")

    meta.sort(key=lambda m: (GROUP_ORDER.index(m["group"]), m["slug"]))
    meta_path = Path(__file__).resolve().parent / "_qt_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"copied {len(meta)} cases → {CASES}")
    print(f"meta → {meta_path}")
    print(f"dropped keep→trivial: {sum(1 for u in manifest if u.get('verdict')=='keep' and u['unit'] not in KEEP)}")


def _drop_reason(u: dict) -> str:
    unit = u["unit"]
    title = u.get("title") or unit
    hint = u.get("topic_hint") or ""
    # heuristics
    if any(x in unit for x in ("hello", "helloworld", "commandcompile", "examples-pro", "qml-pro")):
        return f"drop-trivial：Hello/向导/空工程级（{title}）"
    if unit.startswith("prac-qt-qmlbook-") and unit not in KEEP:
        return f"drop-trivial：QmlBook 跟练与 Qt5/ 自写同主题重复或无实质批注点（{title}）"
    if unit.startswith("prac-qt-qt5-"):
        return f"drop-trivial：Qt5开发及实例跟练无独立内容（{title}）"
    if unit in {
        "qt5-21-layoutbinding",
        "qt5-23-layoutcolumn",
        "qt5-26-layoutcolumn",
        "qt5-54-layout",
        "qt5-55-layout",
        "qt5-59-stackwidget",
        "qt5-25-layoutflow",
        "qt5-43-checkbox",
        "qt5-82-networkinformation",
    }:
        return f"drop-trivial：与已收同主题布局/网络条目重复变体（{title}）"
    if unit.startswith("pyqt-a1") or unit.startswith("pyqt-a2") or unit.startswith("pyqt-a3"):
        return f"drop-trivial：PyQt Hello 级（{title}）"
    if "hello" in title.lower() or "Hello" in title:
        return f"drop-trivial：Hello World 级（{title}）"
    return f"drop-trivial：精选筛除——规模过小或与已收条目重复（{title}；{hint}）"


if __name__ == "__main__":
    main()
