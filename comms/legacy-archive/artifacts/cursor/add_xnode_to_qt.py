#!/usr/bin/env python3
"""Append Practice/XNode to manifest-qt per claude-code FYI; refresh verify/md notes."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
LEGACY = REPO / ".cache" / "legacy-src"
MANIFEST = OUT / "manifest-qt.json"


def first_commit(path: str) -> str:
    out = subprocess.check_output(
        [
            "git",
            "-C",
            str(LEGACY / "Practice"),
            "log",
            "--reverse",
            "--format=%ad",
            "--date=short",
            "--",
            path,
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()
    return out.splitlines()[0] if out else "unknown"


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if any(e["unit"] == "prac-xnode" for e in data):
        print("already present")
        return
    files = subprocess.check_output(
        ["git", "-C", str(LEGACY / "Practice"), "ls-files", "XNode"],
        text=True,
        encoding="utf-8",
    ).splitlines()
    # drop junk .user if any
    files = [f for f in files if ".pro.user" not in f and not f.endswith(".user")]
    # pick earliest among a few reps
    reps = [
        f
        for f in files
        if f.endswith((".cpp", ".h", "CMakeLists.txt"))
    ][:5]
    dates = [first_commit(r) for r in reps]
    dates = [d for d in dates if d != "unknown"]
    entry = {
        "unit": "prac-xnode",
        "title": "XNode（Qt 网络节点：Server/Client/Monitor/Library）",
        "target": "programming/qt",
        "verdict": "keep",
        "canonical": ["Practice/XNode"],
        "duplicates": [],
        "first_commit": min(dates) if dates else "unknown",
        "files": len(files),
        "run": "toolchain",
        "build": "cmake -S Practice/XNode -B build -DCMAKE_PREFIX_PATH=C:/Qt/6.8.1/msvc2022_64 && cmake --build build",
        "build_checked": False,
        "topic_hint": "archive.qt.network",
        "quality_notes": "多 CMake 子工程（Application/Client/Monitor/NodeLibrary/NodeServer/StandAloneNode）；根目录另有散落 client.cpp/server.cpp/xnode.*，职责边界需整理；网络与 UI 耦合点在 Application/Monitor",
        "reason": "claude-code FYI（20261021-153742）：按内容归 programming/qt，并为一个工程单元",
        "_xnode_files": files,
    }
    data.append({k: v for k, v in entry.items() if not k.startswith("_")})
    data.sort(
        key=lambda e: (
            {"keep": 0, "drop-third-party": 1, "drop-junk": 2}.get(e["verdict"], 9),
            e.get("topic_hint", ""),
            e["unit"],
        )
    )
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # extend sidecar coverage
    side_path = OUT / "_qt_unit_files.json"
    if side_path.is_file():
        side = json.loads(side_path.read_text(encoding="utf-8"))
    else:
        side = {"missing": [], "unit_files": {}, "dup_unit_files": {}}
    side["unit_files"]["prac-xnode"] = [f"Practice/{f}" for f in files]
    side_path.write_text(json.dumps(side, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # append note to md
    md = OUT / "manifest-qt.md"
    if md.is_file():
        text = md.read_text(encoding="utf-8")
        note = (
            f"\n## 补录（{datetime.now().isoformat(timespec='seconds')}）\n\n"
            f"- 按 claude-code FYI：并入 `Practice/XNode` 为 keep 单元 `prac-xnode`（files={len(files)}，"
            f"topic=`archive.qt.network`，first={entry['first_commit']}）。\n"
            f"- 覆盖校验需把 XNode 54 个文件算进 scoped（见 verify-qt-xnode.txt）。\n"
        )
        md.write_text(text + note, encoding="utf-8")

    # xnode-specific verify snippet
    (OUT / "verify-qt-xnode.txt").write_text(
        f"prac-xnode files={len(files)}\n" + "\n".join(f"Practice/{f}" for f in files) + "\n",
        encoding="utf-8",
    )
    print(f"added prac-xnode files={len(files)} first={entry['first_commit']}")


if __name__ == "__main__":
    main()
