#!/usr/bin/env python3
"""Try qmake+nmake/jom on representative keep units. Does NOT modify sources."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
LEGACY = REPO / ".cache" / "legacy-src"
OUT = Path(__file__).resolve().parent
MANIFEST = OUT / "manifest-qt.json"
QT_BIN = Path(r"C:\Qt\6.8.1\msvc2022_64\bin")
QMAKE = QT_BIN / "qmake.exe"

# topic -> prefer these unit id substrings
SAMPLES = {
    "archive.qt.signals-slots": ["signal"],
    "archive.qt.layout": ["layout", "splitter"],
    "archive.qt.windows-dialogs": ["window", "login", "tray", "embed"],
    "archive.qt.qml-quick": ["quick", "qml", "helloqml"],
    "archive.qt.basics": ["hello", "widget", "menu"],
    "archive.qt.network": ["network", "process"],
    "archive.qt.charts": ["chart"],
    "archive.qt.model-view": ["student", "model"],
    "archive.qt.designer": ["designer"],
    "archive.qt.pyqt": ["pyqt", "python"],
}


def find_vcvars() -> Path | None:
    candidates = [
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def pick_units(data: list[dict]) -> list[dict]:
    keeps = [e for e in data if e["verdict"] == "keep"]
    picked = []
    used = set()
    for topic, keys in SAMPLES.items():
        pool = [e for e in keeps if e.get("topic_hint") == topic]
        n = 0
        for e in pool:
            if n >= 3:
                break
            blob = (e["unit"] + " " + e["canonical"][0]).lower()
            if keys and not any(k in blob for k in keys):
                # still allow if pool small
                if len(pool) > 6:
                    continue
            if e["unit"] in used:
                continue
            # need a .pro under canonical
            can = e["canonical"][0]
            repo, rel = can.split("/", 1)
            base = LEGACY / repo / rel
            pros = list(base.rglob("*.pro")) if base.is_dir() else []
            pros = [p for p in pros if ".pro.user" not in p.name]
            if not pros and topic != "archive.qt.pyqt":
                continue
            picked.append(e)
            used.add(e["unit"])
            n += 1
        # fill up to 2 even without key match
        for e in pool:
            if n >= 2:
                break
            if e["unit"] in used:
                continue
            can = e["canonical"][0]
            repo, rel = can.split("/", 1)
            base = LEGACY / repo / rel
            if not base.is_dir():
                continue
            pros = [p for p in base.rglob("*.pro") if ".pro.user" not in p.name]
            py = list(base.rglob("*.py"))
            if not pros and not py:
                continue
            picked.append(e)
            used.add(e["unit"])
            n += 1
    return picked


def try_build_pro(pro: Path, work: Path) -> tuple[bool, str]:
    # copy sources into work (read-only source → temp)
    src_dir = pro.parent
    dst = work / src_dir.name
    shutil.copytree(
        src_dir,
        dst,
        ignore=shutil.ignore_patterns(
            "*.pro.user*",
            "debug",
            "release",
            "Debug",
            "Release",
            "build*",
            "*.exe",
            "*.obj",
            "Makefile*",
        ),
    )
    pro_dst = dst / pro.name
    vcvars = find_vcvars()
    if not vcvars:
        return False, "vcvars64.bat not found"
    # run in cmd with vcvars
    script = work / "build.cmd"
    script.write_text(
        f'@echo off\n'
        f'call "{vcvars}"\n'
        f'cd /d "{dst}"\n'
        f'"{QMAKE}" "{pro_dst.name}" -spec win32-msvc\n'
        f'if errorlevel 1 exit /b 1\n'
        f'where jom >nul 2>&1 && jom /nologo || nmake /nologo\n',
        encoding="utf-8",
    )
    try:
        r = subprocess.run(
            ["cmd", "/c", str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            cwd=str(dst),
        )
    except subprocess.TimeoutExpired:
        return False, "timeout 180s"
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    lines = [ln for ln in out.splitlines() if ln.strip()]
    head = " | ".join(lines[:3])[:300]
    if r.returncode == 0:
        return True, f"OK qmake+nmake; {head}"
    # extract useful error
    err = [ln for ln in lines if "error" in ln.lower() or "Error" in ln]
    msg = err[0] if err else (lines[-1] if lines else f"rc={r.returncode}")
    return False, f"FAIL rc={r.returncode}: {msg[:240]}"


def try_py(pyfile: Path) -> tuple[bool, str]:
    r = subprocess.run(
        ["py", "-3", "-c", "import PyQt5; print(PyQt5.QtCore.QT_VERSION_STR)"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        r2 = subprocess.run(
            ["py", "-3", "-c", "import PySide6; print(PySide6.__version__)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r2.returncode != 0:
            return False, "PyQt5/PySide6 not importable on this machine"
        return False, f"PySide6={r2.stdout.strip()} present but sources are PyQt5; not executed"
    # syntax check only (GUI would hang)
    r3 = subprocess.run(
        ["py", "-3", "-m", "py_compile", str(pyfile)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r3.returncode == 0:
        return True, f"py_compile OK; PyQt5={r.stdout.strip()}"
    return False, f"py_compile FAIL: {(r3.stderr or '')[:200]}"


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    picked = pick_units(data)
    results = []
    print(f"testing {len(picked)} units; qmake={QMAKE.is_file()}")
    with tempfile.TemporaryDirectory(prefix="athena-qt-build-") as td:
        work = Path(td)
        for e in picked:
            can = e["canonical"][0]
            repo, rel = can.split("/", 1)
            base = LEGACY / repo / rel
            print(f"\n## {e['unit']}  ({can})")
            if e.get("topic_hint") == "archive.qt.pyqt" or list(base.rglob("*.py")):
                pys = sorted(base.rglob("*.py"))
                if not pys:
                    ok, msg = False, "no .py found"
                else:
                    ok, msg = try_py(pys[0])
            else:
                pros = sorted(
                    p for p in base.rglob("*.pro") if ".pro.user" not in p.name
                )
                if not pros:
                    ok, msg = False, "no .pro"
                else:
                    # prefer shallowest .pro
                    pros.sort(key=lambda p: (len(p.parts), len(p.name)))
                    ok, msg = try_build_pro(pros[0], work / e["unit"])
            print(("PASS" if ok else "FAIL"), msg)
            results.append(
                {
                    "unit": e["unit"],
                    "canonical": can,
                    "topic_hint": e.get("topic_hint"),
                    "ok": ok,
                    "detail": msg,
                }
            )
            # update manifest in memory
            for m in data:
                if m["unit"] == e["unit"]:
                    m["build_checked"] = True
                    m["build"] = msg
                    break

    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = OUT / "build-test-qt.txt"
    lines = [
        f"qmake: {QMAKE}",
        f"tested: {len(results)}",
        f"pass: {sum(1 for r in results if r['ok'])}",
        f"fail: {sum(1 for r in results if not r['ok'])}",
        "",
    ]
    for r in results:
        lines.append(f"{'PASS' if r['ok'] else 'FAIL'}  {r['unit']}  {r['canonical']}")
        lines.append(f"  topic={r['topic_hint']}")
        lines.append(f"  {r['detail']}")
        lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    print("\nwrote", report)
    print("updated build_checked in", MANIFEST)


if __name__ == "__main__":
    main()
