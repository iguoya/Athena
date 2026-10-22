# -*- coding: utf-8 -*-
"""Merge _qt_meta.json + _notes_batch_{a,b,c}.json → qt/content/archive.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE / "qt" / "content"
CASES = CONTENT / "cases"

GROUP_LABEL = {
    "signals-slots": "信号与槽",
    "basics": "基础控件",
    "layout": "布局",
    "windows-dialogs": "窗口与对话框",
    "model-view": "Model/View",
    "network": "网络与进程",
    "charts": "图表",
    "designer": "Designer",
    "qml-quick": "QML/Quick",
    "pyqt": "PyQt",
    "other": "综合小项目",
    "misc-app": "宿主应用",
}

TITLE_MAP = {
    # override from meta titles already good
}


def load_notes() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name in ("_notes_batch_a.json", "_notes_batch_b.json", "_notes_batch_c.json"):
        arr = json.loads((HERE / name).read_text(encoding="utf-8"))
        for item in arr:
            out[item["case"]] = item
    return out


def validate_notes(case: str, notes: list[dict]) -> list[str]:
    problems = []
    case_dir = CASES / case
    kinds = set()
    if len(notes) < 3:
        problems.append(f"{case}: notes < 3")
    for n in notes:
        kinds.add(n.get("kind"))
        f = case_dir / n["file"]
        if not f.is_file():
            problems.append(f"{case}: missing {n['file']}")
            continue
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        end = n.get("end", n["line"])
        if not (1 <= n["line"] <= end <= len(lines)):
            problems.append(f"{case}: bad line {n['file']}:{n['line']}-{end} (n={len(lines)})")
        if len(n.get("text", "")) < 20:
            problems.append(f"{case}: short note")
    if len(kinds) < 2:
        problems.append(f"{case}: kinds < 2")
    return problems


def main() -> None:
    meta = json.loads((HERE / "_qt_meta.json").read_text(encoding="utf-8"))
    notes_by = load_notes()
    missing = [m["case"] for m in meta if m["case"] not in notes_by]
    if missing:
        raise SystemExit(f"missing notes for: {missing}")

    problems: list[str] = []
    topics = []
    for m in meta:
        n = notes_by[m["case"]]
        problems += validate_notes(m["case"], n["notes"])
        group = m["group"]
        label = GROUP_LABEL.get(group, group)
        guide = n.get("guide_line") or f"[{label}] {m['title']}"
        if not guide.startswith("["):
            guide = f"[{label}] {guide}"

        sources = n.get("sources") or m["sources"]
        # ensure sources exist
        sources = [s for s in sources if (CASES / m["case"] / s).is_file()]
        if not sources:
            sources = m["sources"][:10]

        summary = n["summary"]
        if m.get("build_checked_pass"):
            if "实测 Qt 6.8.1 通过" not in summary:
                summary = summary.rstrip("。") + "。实测 Qt 6.8.1 通过。"

        run_note = n.get("run_note") or "需要 Qt 5/6 + qmake 或 CMake"
        if m["slug"] in ("pyqtsignal", "pyqtdialog"):
            run_note = "需要 PyQt5"

        block = {
            "type": "archive",
            "case": m["case"],
            "sources": sources,
            "std": n.get("std") or "c++17",
            "run": "toolchain",
            "run_note": run_note,
            "summary": summary,
            "origin": {
                "repo": m["repo"],
                "path": m["path"],
                "first_commit": m["first_commit"],
                "duplicates": m.get("duplicates") or [],
            },
            "notes": [],
        }
        for note in n["notes"]:
            item = {
                "file": note["file"],
                "line": note["line"],
                "kind": note["kind"],
                "text": note["text"],
            }
            if "end" in note and note["end"] != note["line"]:
                item["end"] = note["end"]
            block["notes"].append(item)

        topic = {
            "id": f"qt.arc.{m['slug']}",
            "title": m["title"],
            "difficulty": m["difficulty"],
            "mastery_goal": "understand",
            "knowledge_type": "skill",
            "requires": [],
            "track": "archive",
            "guide_line": guide,
            "weight": "了解",
            "outline": n["outline"],
            "lesson": {
                "blocks": [
                    {"type": "lead", "text": n["lead"]},
                    block,
                    {
                        "type": "callout",
                        "tone": "info",
                        "title": "对照现行讲解",
                        "text": "主课表尚在建设；本条先作历史归档阅读。并入 `programming/qt` 后，再把对照指向对应主线章节。",
                    },
                ]
            },
        }
        topics.append(topic)

    if problems:
        print("VALIDATION ISSUES:")
        for p in problems:
            print(" ", p)
        raise SystemExit(1)

    archive = {
        "tracks": [{"id": "archive", "title": "历史归档", "color": "#a08c64"}],
        "chapters": [
            {
                "id": "archive",
                "title": "历史归档 · 早年 Qt 练习的整理与批注",
                "track": "archive",
                "layer": "archive",
                "summary": "从 2020–2023 年散落在 Qt5、Practice、Linux 等旧仓库里的 Qt/QML/PyQt 练习中精选而来（ADR 0176）：代码原样保留，应用内只读（run=toolchain），另有行级批注指出写法与程序组织上的不足（含 Qt5→Qt6 可移植性）。本章不属于主线，不计入进度，留待人工审视后决定并入、保留或删除。",
                "topics": topics,
            }
        ],
    }
    out = CONTENT / "archive.json"
    out.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} with {len(topics)} topics")


if __name__ == "__main__":
    main()
