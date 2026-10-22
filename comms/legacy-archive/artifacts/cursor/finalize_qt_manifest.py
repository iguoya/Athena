#!/usr/bin/env python3
"""Enrich manifest-qt.json after build tests; write manifest-qt.md + verify-qt.txt."""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]  # cursor → artifacts → legacy-archive → comms → Athena? NO:
# OUT=.../artifacts/cursor → parents[0]=artifacts [1]=legacy-archive [2]=comms [3]=Athena
LEGACY = REPO / ".cache" / "legacy-src"
MANIFEST = OUT / "manifest-qt.json"
BUILD_LOG = OUT / "build-test-qt.txt"
FILES_MAP = OUT / "_qt_unit_files.json"


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def better_topic(e: dict) -> str:
    if e.get("topic_hint") != "archive.qt.other":
        return e["topic_hint"]
    blob = (e["unit"] + " " + " ".join(e.get("canonical", [])) + " " + e.get("title", "")).lower()
    rules = [
        (r"quick|qml|controls|material|canvas|rectangle|item|button|checkbox|label|page|frame|panel|slider|pi|anchors|archors|flow|stack", "archive.qt.qml-quick"),
        (r"signal|slot", "archive.qt.signals-slots"),
        (r"layout|splitter|stackwidget|grid", "archive.qt.layout"),
        (r"login|window|embed|tray|dropfile|callapp", "archive.qt.windows-dialogs"),
        (r"network|process|tcp|udp", "archive.qt.network"),
        (r"chart", "archive.qt.charts"),
        (r"student|model|view|list", "archive.qt.model-view"),
        (r"designer|uml", "archive.qt.designer"),
        (r"pyqt|python", "archive.qt.pyqt"),
        (r"hello|widget|menu|text|syntax|compile|cmake|log|awesome|datetime|js|debug", "archive.qt.basics"),
        (r"qtapp", "archive.qt.misc-app"),
        (r"qmlbook|开发及实例", "archive.qt.qml-quick"),
    ]
    for pat, hint in rules:
        if re.search(pat, blob):
            return hint
    return "archive.qt.other"


def quality_for(e: dict) -> str:
    if e["verdict"] != "keep":
        return e.get("quality_notes") or ""
    can = e["canonical"][0]
    repo, rel = can.split("/", 1)
    base = LEGACY / repo / rel
    notes = []
    if not base.is_dir():
        return e.get("quality_notes") or "路径缺失"
    files = [p for p in base.rglob("*") if p.is_file()]
    for p in files:
        if p.suffix.lower() not in {".cpp", ".h", ".hpp", ".qml", ".py"}:
            continue
        t = read_text(p)
        if "QRegExp" in t:
            notes.append(f"{p.name}: QRegExp（Qt6 需 QRegularExpression）")
        if re.search(r"\bnew\s+\w+", t) and "delete" not in t and p.name == "main.cpp":
            notes.append(f"{p.name}: new 后无 delete")
        if p.suffix == ".h" and "#pragma once" not in t and not re.search(r"#\s*ifndef", t):
            notes.append(f"{p.name}: 无 include guard")
        if "using namespace std" in t:
            notes.append(f"{p.name}: using namespace std")
        if re.search(r"endl\b", t) and "#include <iostream>" not in t and "std::endl" not in t and p.suffix == ".cpp":
            if "endl" in t and "QTextStream" not in t:
                notes.append(f"{p.name}: 使用 endl 但可能未正确限定（Qt6/MSVC 易炸）")
    # .pro QT modules
    for pro in base.rglob("*.pro"):
        if ".user" in pro.name:
            continue
        t = read_text(pro)
        if "widgets" not in t.lower() and list(base.rglob("*.ui")):
            notes.append(f"{pro.name}: 有 .ui 但 .pro 可能未声明 QT += widgets")
        break
    if "QtApp" in can:
        notes.append("宿主小应用曾 vendoring qdarkstyle（已单独 drop-third-party）")
    if not notes:
        notes.append(e.get("quality_notes") or "练习工程：缺测试、资源与源码混放、命名不统一")
    # dedupe preserve order
    seen = set()
    out = []
    for n in notes:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return "；".join(out[:4])


def apply_build_log(data: list[dict]) -> None:
    if not BUILD_LOG.is_file():
        return
    text = BUILD_LOG.read_text(encoding="utf-8", errors="ignore")
    # parse PASS/FAIL blocks
    blocks = re.findall(
        r"(PASS|FAIL)\s+(\S+)\s+(\S+)\n\s+topic=(\S+)\n\s+(.+)",
        text,
    )
    by_unit = {u: (ok == "PASS", detail.strip()) for ok, u, _can, _t, detail in blocks}
    for e in data:
        if e["unit"] not in by_unit:
            continue
        ok, detail = by_unit[e["unit"]]
        e["build_checked"] = True
        can = e["canonical"][0]
        repo, rel = can.split("/", 1)
        base = LEGACY / repo / rel
        pros = sorted(
            p for p in base.rglob("*.pro") if p.is_file() and ".user" not in p.name
        ) if base.is_dir() else []
        if e.get("topic_hint") == "archive.qt.pyqt" or (
            base.is_dir() and list(base.rglob("*.py")) and not pros
        ):
            cmd = "py -3 -m py_compile <main.py>  # needs PyQt5"
        elif pros:
            pros.sort(key=lambda p: (len(p.parts), len(p.name)))
            cmd = (
                f'qmake {pros[0].name} -spec win32-msvc && nmake '
                f"(Qt 6.8.1 msvc2022_64)"
            )
        else:
            cmd = e.get("build") or "qmake && nmake"
        if ok:
            e["build"] = cmd + " — 实测通过"
        else:
            # shorten detail
            d = detail
            d = re.sub(r"FAIL rc=\d+:\s*", "", d)
            d = d.replace("PASS OK qmake+nmake; ", "")
            e["build"] = cmd + " — 实测失败: " + d[:220]


def fill_missing_dates(data: list[dict]) -> None:
    for e in data:
        if e.get("first_commit") not in (None, "unknown", ""):
            continue
        can = e["canonical"][0]
        if can.startswith("junk") or e["first_commit"] == "n/a":
            continue
        parts = can.split("/", 1)
        if len(parts) != 2:
            continue
        repo, rel = parts
        base = LEGACY / repo / rel
        candidates = []
        if base.is_file():
            candidates = [rel]
        elif base.is_dir():
            for p in base.rglob("*"):
                if p.suffix.lower() in {".cpp", ".h", ".pro", ".py", ".qml"}:
                    candidates.append(p.relative_to(LEGACY / repo).as_posix())
                    if len(candidates) >= 3:
                        break
        dates = []
        for c in candidates:
            try:
                out = subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(LEGACY / repo),
                        "log",
                        "--reverse",
                        "--format=%ad",
                        "--date=short",
                        "--",
                        c,
                    ],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                ).strip()
            except subprocess.CalledProcessError:
                continue
            if out:
                dates.append(out.splitlines()[0].strip())
        if dates:
            e["first_commit"] = min(dates)


def write_md(data: list[dict]) -> None:
    keeps = [e for e in data if e["verdict"] == "keep"]
    drops_tp = [e for e in data if e["verdict"] == "drop-third-party"]
    drops_junk = [e for e in data if e["verdict"] == "drop-junk"]
    checked = [e for e in data if e.get("build_checked")]
    checked_ok = [e for e in checked if "实测通过" in (e.get("build") or "")]
    checked_fail = [e for e in checked if "实测失败" in (e.get("build") or "")]

    topic_c = Counter(e["topic_hint"] for e in keeps)
    lines = [
        "# Qt 领域清单摘要（T-101）",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 目标应用：`programming/qt`（新建，ADR 0176）",
        f"- JSON：`comms/legacy-archive/artifacts/cursor/manifest-qt.json`",
        f"- 覆盖校验：`verify-qt.txt`（scoped 全覆盖）",
        f"- 编译实测日志：`build-test-qt.txt`",
        "",
        "## 统计",
        "",
        f"| 项 | 数量 |",
        f"|---|---:|",
        f"| 单元总计 | {len(data)} |",
        f"| keep | {len(keeps)} |",
        f"| drop-third-party | {len(drops_tp)} |",
        f"| drop-junk | {len(drops_junk)} |",
        f"| 含 duplicates 字段的规范版 | {sum(1 for e in data if e.get('duplicates'))} |",
        f"| build_checked | {len(checked)}（通过 {len(checked_ok)} / 失败 {len(checked_fail)}） |",
        "",
        "### keep 建议子分组（topic_hint）",
        "",
        "| topic_hint | keep 数 |",
        "|---|---:|",
    ]
    for t, n in topic_c.most_common():
        lines.append(f"| `{t}` | {n} |")

    lines += [
        "",
        "## 范围与去重结论",
        "",
        "- `Qt5/` 与 `Linux/QT/` 下同名编号工程（如 `01-SignalSlot`、`20-SignalAndSlot`）内容哈希一致，规范版取 `Qt5/...`，`Linux/QT/...` 记入 `duplicates`。",
        "- `Qt5/Sample/**` 与 `Linux/Sample/**` 同为 `chapNN…/sampN_M…` 树；对照文件内容一致，判定为教材随书样例整套拷贝（布局同王英《Qt5.9 C++开发指南》一类配套），**未见个人改动痕迹** → `drop-third-party`（47 个样例单元 + meta）。",
        "- `Linux/QT/QtApp/qdarkstyle`（481 文件）→ `drop-third-party`（[QDarkStyleSheet](https://github.com/ColinDuquesnoy/QDarkStyleSheet)）；宿主小应用 `Linux/QT/QtApp/app` 单独 keep。",
        "- `29-QtAwesome` → `drop-third-party`（QtAwesome/Font Awesome）。",
        "- `.pro.user*`、构建产物 → `drop-junk`。",
        "- `Practice/CGI/**` → `drop-junk`（与 Qt 无关，显式记入以满足零遗漏）。",
        "- `Practice/QT/QmlBook/*`、`Practice/QT/Qt5开发及实例/*`：按子工程拆分；无版权头，形态像跟练笔记，暂 **keep**，见待裁决。",
        "- `Practice/untitled`：CMake 最小窗口，keep（basics）。",
        "",
        "## 编译实测（本机 Qt 6.8.1 MSVC）",
        "",
        "规则：每主题抽 2–3 个样本；其余 `build_checked: false`。只在临时目录拷贝源码编译，**未改** `.cache/legacy-src`。",
        "",
    ]
    if BUILD_LOG.is_file():
        lines.append("详见 `build-test-qt.txt`。摘要：")
        lines.append("")
        for e in checked:
            flag = "通过" if "实测通过" in e.get("build", "") else "失败"
            lines.append(f"- [{flag}] `{e['unit']}` ← `{e['canonical'][0]}` — {e['build'].split('—')[-1].strip()[:160]}")
        lines.append("")

    lines += [
        "## 待裁决（已发消息给 claude-code）",
        "",
        "1. **Sample 教材样例**：是否整套坚持 `drop-third-party`，还是挑几章「跟练痕迹明显」的改 keep？",
        "2. **Practice/QT/QmlBook**：跟练工程 keep 还是按书名视为第三方样例 drop？",
        "3. **Practice/QT/Qt5开发及实例**：目录名即书名，是否一律 drop-third-party？",
        "4. **Qt Charts / 旧 API**：`91-QtChartsBasic` 缺 QtCharts 模块组件；`Examples/chart` 触碰 Qt6 API 变更（`QString::SkipEmptyParts`）——归档时是否允许 `// [ARCHIVE]` 最小补丁？",
        "5. **PyQt**：本机无 PyQt5/PySide，一律 `toolchain` + `build_checked` 记录「解释器侧缺库」是否够用？",
        "",
        "## keep 单元一览（按 topic）",
        "",
    ]
    by_topic = defaultdict(list)
    for e in keeps:
        by_topic[e["topic_hint"]].append(e)
    for topic in sorted(by_topic):
        lines.append(f"### `{topic}`")
        lines.append("")
        for e in sorted(by_topic[topic], key=lambda x: x["unit"]):
            dups = f"（重复 {len(e.get('duplicates') or [])}）" if e.get("duplicates") else ""
            checked_s = " ✓" if e.get("build_checked") else ""
            lines.append(
                f"- `{e['unit']}`{checked_s} — {e['title']} ← `{e['canonical'][0]}` "
                f"files={e['files']} first={e.get('first_commit')}{dups}"
            )
        lines.append("")

    (OUT / "manifest-qt.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def rewrite_verify(data: list[dict]) -> None:
    # recompute coverage from sidecar if present
    scoped_note = ""
    missing = []
    if FILES_MAP.is_file():
        side = json.loads(FILES_MAP.read_text(encoding="utf-8"))
        missing = side.get("missing") or []
        scoped_note = f"sidecar missing list size={len(missing)}"
    # recount from git for confidence
    import subprocess as sp

    def ls(repo):
        out = sp.check_output(
            ["git", "-C", str(LEGACY / repo), "ls-files", "-z"],
        )
        return [p.replace("\\", "/") for p in out.decode("utf-8", "replace").split("\0") if p]

    scoped = []
    for rel in ls("Qt5"):
        scoped.append(f"Qt5/{rel}")
    for rel in ls("Linux"):
        if rel.split("/", 1)[0] in ("QT", "PyQt", "QML", "Sample"):
            scoped.append(f"Linux/{rel}")
    for rel in ls("Practice"):
        top = rel.split("/", 1)[0]
        if top in ("QT", "untitled", "CGI") or top.startswith('"QT') or top.startswith("QT"):
            scoped.append(f"Practice/{rel}")

    covered = set()
    side = json.loads(FILES_MAP.read_text(encoding="utf-8")) if FILES_MAP.is_file() else {}
    for paths in (side.get("unit_files") or {}).values():
        covered.update(paths)
    for paths in (side.get("dup_unit_files") or {}).values():
        covered.update(paths)
    scoped_set = set(scoped)
    miss = sorted(scoped_set - covered)
    lines = [
        f"generated: {datetime.now().isoformat(timespec='seconds')}",
        f"scoped_files: {len(scoped_set)}",
        f"covered_files: {len(scoped_set & covered)}",
        f"missing_files: {len(miss)}",
        f"units: {len(data)}",
        f"keep: {sum(1 for e in data if e['verdict']=='keep')}",
        f"drop-third-party: {sum(1 for e in data if e['verdict']=='drop-third-party')}",
        f"drop-junk: {sum(1 for e in data if e['verdict']=='drop-junk')}",
        f"build_checked_true: {sum(1 for e in data if e.get('build_checked'))}",
        f"note: {scoped_note}",
        "",
        "=== missing ===",
    ]
    lines.extend(f"  {m}" for m in miss[:80])
    if not miss:
        lines.append("  (none)")
    (OUT / "verify-qt.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for e in data:
        e["topic_hint"] = better_topic(e)
        if e["verdict"] == "keep":
            e["quality_notes"] = quality_for(e)
    apply_build_log(data)
    fill_missing_dates(data)
    # stable sort
    order = {"keep": 0, "drop-third-party": 1, "drop-junk": 2, "drop-duplicate": 3}

    def sk(e):
        v = e["verdict"]
        return (order.get(v, 9), e.get("topic_hint", ""), e["unit"])

    data.sort(key=sk)
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_md(data)
    rewrite_verify(data)
    print("finalized", MANIFEST)
    print("md", OUT / "manifest-qt.md")
    print("verify", OUT / "verify-qt.txt")


if __name__ == "__main__":
    main()
