#!/usr/bin/env python3
"""T-101: scan Qt-related legacy sources → manifest-qt.json/.md + verify-qt.txt.

Read-only over .cache/legacy-src/; writes only under this artifacts/cursor/ dir.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LEGACY = REPO_ROOT / ".cache" / "legacy-src"
OUT_DIR = Path(__file__).resolve().parent

JUNK_SUFFIXES = (
    ".pro.user",
    ".pro.user.",
    ".user",
    ".autosave",
    ".o",
    ".obj",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".a",
    ".lib",
    ".pdb",
    ".ilk",
    ".exp",
    ".qmlc",
    ".jsc",
)
JUNK_NAMES = {
    "CMakeLists.txt.user",
    ".DS_Store",
    "Thumbs.db",
    "Makefile",
    "Makefile.Debug",
    "Makefile.Release",
    ".qmake.stash",
}
JUNK_DIR_PARTS = {
    "debug",
    "release",
    "Debug",
    "Release",
    "build",
    "build-debug",
    "build-release",
    ".moc",
    "moc",
    "ui_bin",
    "object_script",
}

# binary resources that are only kept if referenced by a keep unit
RESOURCE_EXTS = {".bmp", ".ico", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".qrc"}

# third-party markers (path or content)
THIRD_PARTY_PATH_HINTS = [
    (re.compile(r"(?i)qdarkstyle"), "qdarkstyle (third-party Qt stylesheet)"),
    (re.compile(r"(?i)QtAwesome"), "QtAwesome icon font (third-party)"),
    (re.compile(r"(?i)fontawesome"), "Font Awesome (third-party)"),
]


def git_ls(repo: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "-C", str(LEGACY / repo), "ls-files", "-z"],
        stderr=subprocess.DEVNULL,
    )
    if not out:
        return []
    return [p.replace("\\", "/") for p in out.decode("utf-8", "replace").split("\0") if p]


def git_first_commit(repo: str, path: str) -> str | None:
    """Earliest commit date touching path.

    Note: ``--follow`` often returns empty on these legacy trees (copied-in
    blobs); prefer plain ``git log --reverse`` first.
    """
    cmds = [
        ["log", "--reverse", "--format=%ad", "--date=short", "--", path],
        ["log", "--diff-filter=A", "--format=%ad", "--date=short", "--", path],
        ["log", "--follow", "--reverse", "--format=%ad", "--date=short", "--", path],
    ]
    for args in cmds:
        try:
            out = subprocess.check_output(
                ["git", "-C", str(LEGACY / repo), *args],
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            ).strip()
        except subprocess.CalledProcessError:
            continue
        if out:
            return out.splitlines()[0].strip()
    return None


def git_latest_commit(repo: str, path: str) -> str | None:
    try:
        out = subprocess.check_output(
            [
                "git",
                "-C",
                str(LEGACY / repo),
                "log",
                "-1",
                "--format=%ad",
                "--date=short",
                "--",
                path,
            ],
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
    except subprocess.CalledProcessError:
        return None
    return out or None


def norm_content_hash(abs_path: Path) -> tuple[str, str]:
    data = abs_path.read_bytes()
    # binary: hash raw
    if b"\0" in data[:4096]:
        return hashlib.sha256(data).hexdigest(), "bin"
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return hashlib.sha256(data).hexdigest(), "bin"
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), "text"


def is_junk(rel: str) -> bool:
    name = Path(rel).name
    if name in JUNK_NAMES:
        return True
    if name.endswith(".user") or ".pro.user" in name:
        return True
    if name.startswith("ui_") and name.endswith(".h") and "/ui_" in ("/" + rel):
        # generated ui_*.h sometimes committed — treat as junk if beside .ui
        pass
    parts = rel.replace("\\", "/").split("/")
    for p in parts[:-1]:
        if p in JUNK_DIR_PARTS:
            return True
        if p.startswith("build-"):
            return True
    low = name.lower()
    for suf in (".o", ".obj", ".exe", ".dll", ".pdb", ".ilk", ".qmlc", ".jsc"):
        if low.endswith(suf):
            return True
    if name in ("Makefile", "Makefile.Debug", "Makefile.Release", ".qmake.stash"):
        return True
    return False


def collect_scope() -> list[tuple[str, str]]:
    """Return list of (repo, rel_path) in Qt scope."""
    items: list[tuple[str, str]] = []

    for rel in git_ls("Qt5"):
        items.append(("Qt5", rel))

    for rel in git_ls("Linux"):
        top = rel.split("/", 1)[0]
        if top in ("QT", "PyQt", "QML", "Sample"):
            items.append(("Linux", rel))

    for rel in git_ls("Practice"):
        top = rel.split("/", 1)[0]
        # Practice has a weird tracked path starting with quote: "QT/...
        if top in ("QT", "untitled", "CGI") or top.startswith('"QT') or top.startswith("QT"):
            items.append(("Practice", rel))

    return items


def unit_key_for(repo: str, rel: str) -> str | None:
    """Map a file to a unit key (repo-relative project directory)."""
    parts = rel.replace("\\", "/").split("/")

    if repo == "Qt5":
        if rel in (".gitignore", "Qt5.pro", "PyQt5"):
            return f"Qt5/__root__/{Path(rel).name}"
        if parts[0].startswith("Qt5.pro"):
            return "Qt5/__junk__/pro-user"
        if parts[0] == "Sample":
            # Sample/chapXX/sampY_Z/...
            if len(parts) >= 3 and parts[1].startswith("chap"):
                return f"Qt5/Sample/{parts[1]}/{parts[2]}"
            if len(parts) == 1 or (len(parts) == 2 and parts[1].endswith(".pro")):
                return "Qt5/Sample/__meta__"
            return f"Qt5/Sample/{parts[1]}"
        if parts[0] == "Examples":
            if len(parts) >= 2:
                return f"Qt5/Examples/{parts[1]}"
            return "Qt5/Examples"
        if parts[0] == "QML":
            if len(parts) >= 2:
                return f"Qt5/QML/{parts[1]}"
            return "Qt5/QML"
        # numbered lesson dirs
        return f"Qt5/{parts[0]}"

    if repo == "Linux":
        if parts[0] == "Sample":
            if len(parts) >= 3 and parts[1].startswith("chap"):
                return f"Linux/Sample/{parts[1]}/{parts[2]}"
            if len(parts) <= 2 and (len(parts) == 1 or parts[-1].endswith(".pro")):
                return "Linux/Sample/__meta__"
            return f"Linux/Sample/{parts[1]}"
        if parts[0] == "QT":
            if len(parts) == 1:
                return "Linux/QT/__root__"
            if parts[1] == "QtApp":
                # qdarkstyle vendored tree vs the small host app
                if len(parts) >= 3 and parts[2] == "qdarkstyle":
                    return "Linux/QT/QtApp/qdarkstyle"
                if len(parts) >= 3 and parts[2] == "images":
                    return "Linux/QT/QtApp/app"  # resources of host app
                return "Linux/QT/QtApp/app"
            if parts[1].startswith("Qt5.pro"):
                return "Linux/QT/__junk__/pro-user"
            return f"Linux/QT/{parts[1]}"
        if parts[0] == "PyQt":
            if len(parts) >= 2:
                return f"Linux/PyQt/{parts[1]}"
            return "Linux/PyQt"
        if parts[0] == "QML":
            if len(parts) >= 2:
                return f"Linux/QML/{parts[1]}"
            return "Linux/QML"

    if repo == "Practice":
        top = parts[0]
        if top == "CGI" or top.startswith("CGI"):
            return f"Practice/CGI/{parts[1] if len(parts) > 1 else '__root__'}"
        if top == "untitled":
            return "Practice/untitled"
        if top == "QT" or top.startswith('"QT') or top.startswith("QT"):
            # Practice/QT/<book-or-folder>/<project>/...
            if len(parts) >= 3:
                return f"Practice/QT/{parts[1]}/{parts[2]}"
            if len(parts) >= 2:
                return f"Practice/QT/{parts[1]}"
            return "Practice/QT"

    return f"{repo}/{'/'.join(parts[:2])}"


def topic_hint_for(unit_path: str, title: str) -> str:
    u = unit_path.lower()
    t = title.lower()
    blob = u + " " + t
    rules = [
        (r"pyqt|python", "archive.qt.pyqt"),
        (r"qml|quick|controls|material|canvas|rectangle|anchors|archors", "archive.qt.qml-quick"),
        (r"signal|slot", "archive.qt.signals-slots"),
        (r"layout|splitter|stackwidget|grid|flow|column|box", "archive.qt.layout"),
        (r"dialog|login|window|multi|embed|tray|systemtray", "archive.qt.windows-dialogs"),
        (r"model|view|table|list|tree|student", "archive.qt.model-view"),
        (r"database|sql|sqlite", "archive.qt.database"),
        (r"network|http|tcp|udp|process", "archive.qt.network"),
        (r"chart|datavis|visualization", "archive.qt.charts"),
        (r"multimedia|audio|video|camera", "archive.qt.multimedia"),
        (r"sample/chap", "archive.qt.book-sample"),
        (r"designer|ui\.|forms", "archive.qt.designer"),
        (r"cgi", "drop-or-misc"),
        (r"hello|widget|menu|texteditor|datetime|syntax|compile|cmake", "archive.qt.basics"),
    ]
    for pat, hint in rules:
        if re.search(pat, blob):
            return hint
    return "archive.qt.other"


def slugify(unit_path: str) -> str:
    s = unit_path.lower()
    s = s.replace("linux/qt/", "qt-")
    s = s.replace("linux/sample/", "sample-")
    s = s.replace("linux/pyqt/", "pyqt-")
    s = s.replace("linux/qml/", "qml-")
    s = s.replace("qt5/sample/", "sample-")
    s = s.replace("qt5/", "qt5-")
    s = s.replace("practice/qt/", "prac-qt-")
    s = s.replace("practice/", "prac-")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s[:80]


def read_head(abs_path: Path, n: int = 40) -> str:
    try:
        data = abs_path.read_bytes()[:4000]
    except OSError:
        return ""
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def detect_third_party(unit_path: str, files: list[str], repo: str) -> str | None:
    for pat, reason in THIRD_PARTY_PATH_HINTS:
        if pat.search(unit_path):
            return reason
        for f in files:
            if pat.search(f):
                return reason
    # Sample book: look for WangYing / 王英 / Qt5.9 etc.
    for f in files[:20]:
        if not f.endswith((".cpp", ".h", ".pro", ".md", ".txt")):
            continue
        head = read_head(LEGACY / repo / f)
        if re.search(r"王英|Wang\s*Ying|Qt5\.9|清华大学出版社|电子工业出版社.*Qt", head):
            return "Qt book companion sample (detected author/publisher in headers)"
        if "Copyright" in head and re.search(r"(?i) Digia|The Qt Company|Nokia", head):
            if "Sample/" in unit_path or "/chap" in unit_path:
                return "Qt book/official sample copyright header"
    # Sample tree naming convention sampN_M is classic 王英《Qt5.9 C++开发指南》
    if "/Sample/" in unit_path or unit_path.endswith("/Sample"):
        if re.search(r"chap\d+|samp\d+_", unit_path):
            return "Likely 《Qt5.9 C++开发指南》(王英) companion samples (chap*/samp* layout)"
    return None


def quality_notes_for(repo: str, unit_path: str, files: list[str]) -> str:
    notes = []
    abs_files = [LEGACY / repo / f for f in files if (LEGACY / repo / f).is_file()]
    cpp = [p for p in abs_files if p.suffix.lower() in (".cpp", ".cxx", ".cc", ".c")]
    hdr = [p for p in abs_files if p.suffix.lower() in (".h", ".hpp")]
    # include guard
    for h in hdr[:5]:
        text = read_head(h, 80)
        if text and "#pragma once" not in text and not re.search(r"#ifndef\s+\w+", text):
            notes.append(f"{h.name} 缺 include guard / #pragma once")
            break
    # new without delete in main
    for c in cpp[:5]:
        text = read_head(c, 200)
        if "new " in text and "delete " not in text and c.name == "main.cpp":
            notes.append(f"{c.name} 用 new 创建窗口/对象但未见 delete（依赖进程退出回收）")
            break
    # QRegExp (Qt5 API removed/changed in Qt6)
    for p in abs_files:
        if p.suffix.lower() not in (".cpp", ".h"):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "QRegExp" in t:
            notes.append(f"{p.name} 使用 QRegExp（Qt6 需改 QRegularExpression）")
            break
    if "QtApp" in unit_path:
        notes.append("QtApp 子树体量大、编号混乱，疑似练习堆叠未整理")
    if not notes:
        # peek main
        for c in cpp[:3]:
            t = read_head(c)
            if "TODO" in t or "FIXME" in t:
                notes.append(f"{c.name} 含 TODO/FIXME")
                break
        if not notes:
            notes.append("练习级工程：缺测试、命名口语化、.pro 未分 debug/release 资源")
    return "；".join(notes[:3])


def pick_build_cmd(repo: str, unit_rel: str, files: list[str]) -> str:
    pros = [f for f in files if f.endswith(".pro") and not f.endswith(".pro.user")]
    cmakes = [f for f in files if Path(f).name == "CMakeLists.txt"]
    pyfiles = [f for f in files if f.endswith(".py")]
    qml_only = [f for f in files if f.endswith(".qml")]
    if pros:
        # shortest .pro at unit root preferred
        pros_sorted = sorted(pros, key=lambda p: (p.count("/"), len(p)))
        return f'qmake "{pros_sorted[0]}" && nmake/mingw32-make (Qt 6.8.1 msvc2022_64)'
    if cmakes:
        return f'cmake -S . -B build -DCMAKE_PREFIX_PATH=C:/Qt/6.8.1/msvc2022_64 && cmake --build build'
    if pyfiles:
        return f"python {Path(pyfiles[0]).name}  # needs PyQt5/PySide"
    if qml_only:
        return "qmlscene / qqml (Qt Quick runtime)"
    return "unknown — inspect sources"


def unit_title(unit_path: str) -> str:
    leaf = unit_path.rstrip("/").split("/")[-1]
    if leaf.startswith("__"):
        return leaf
    return leaf


def main() -> int:
    if not LEGACY.is_dir():
        print("MISSING", LEGACY, file=sys.stderr)
        return 1

    print("collecting scope…")
    scoped = collect_scope()
    print(f"  {len(scoped)} tracked files in scope")

    # group into units
    units: dict[str, list[tuple[str, str]]] = defaultdict(list)
    junk_files: list[tuple[str, str]] = []
    for repo, rel in scoped:
        if is_junk(rel):
            junk_files.append((repo, rel))
            continue
        uk = unit_key_for(repo, rel)
        if uk is None:
            junk_files.append((repo, rel))
            continue
        units[uk].append((repo, rel))

    print(f"  {len(units)} raw units, {len(junk_files)} junk files")

    # content fingerprint per unit (sorted file hashes of text/code only)
    def unit_fingerprint(repo: str, files: list[str], unit_key: str) -> str:
        """Content fingerprint; paths are relative to the unit directory so
        Qt5/01-SignalSlot and Linux/QT/01-SignalSlot can match."""
        h = hashlib.sha256()
        code_exts = {
            ".cpp",
            ".h",
            ".hpp",
            ".c",
            ".cc",
            ".cxx",
            ".qml",
            ".ui",
            ".pro",
            ".qrc",
            ".py",
            ".js",
            ".cmake",
            ".txt",
            ".md",
            ".json",
        }
        # unit_key is like "Qt5/01-SignalSlot" or "Linux/QT/01-SignalSlot"
        # strip repo prefix to get dir under that repo
        unit_dir = unit_key.split("/", 1)[1] if "/" in unit_key else ""
        rels = sorted(
            f
            for f in files
            if Path(f).suffix.lower() in code_exts or Path(f).name == "CMakeLists.txt"
        )
        if not rels:
            rels = sorted(f for f in files if Path(f).suffix.lower() not in RESOURCE_EXTS)
        for f in rels:
            p = LEGACY / repo / f
            if not p.is_file():
                continue
            digest, _ = norm_content_hash(p)
            if unit_dir and (f == unit_dir or f.startswith(unit_dir + "/")):
                within = f[len(unit_dir) :].lstrip("/")
            else:
                within = Path(f).name
            h.update(within.encode())
            h.update(digest.encode())
        return h.hexdigest()

    unit_meta: dict[str, dict] = {}
    for uk, pairs in units.items():
        # all pairs share same repo? Sample exists in both — unit key includes repo
        by_repo: dict[str, list[str]] = defaultdict(list)
        for repo, rel in pairs:
            by_repo[repo].append(rel)
        # should be single repo per unit key
        repo = next(iter(by_repo))
        files = sorted(by_repo[repo])
        fp = unit_fingerprint(repo, files, uk)
        # first commit: use a representative source file
        reps = [
            f
            for f in files
            if Path(f).suffix.lower() in {".cpp", ".py", ".qml", ".pro", ".h"}
        ] or files
        first = None
        latest = None
        for rep in reps[:3]:
            d = git_first_commit(repo, rep)
            if d and (first is None or d < first):
                first = d
            d2 = git_latest_commit(repo, rep)
            if d2 and (latest is None or d2 > latest):
                latest = d2
        unit_meta[uk] = {
            "repo": repo,
            "files": files,
            "fingerprint": fp,
            "first": first,
            "latest": latest or first,
            "file_count": len(files),
        }

    # Force-merge obvious cross-repo clones by leaf name when fingerprints
    # already match OR when both sides are numbered lesson dirs with identical
    # relative file sets (belt-and-suspenders for Qt5/* ↔ Linux/QT/*).
    leaf_groups: dict[str, list[str]] = defaultdict(list)
    for uk in unit_meta:
        if uk.startswith("Qt5/") and uk.count("/") == 1:
            leaf_groups[uk.split("/")[-1]].append(uk)
        elif uk.startswith("Linux/QT/") and uk.count("/") == 2:
            leaf_groups[uk.split("/")[-1]].append(uk)
        elif "/Sample/" in uk:
            # chapXX/sampYY leaf
            leaf_groups["sample:" + "/".join(uk.split("/")[-2:])].append(uk)

    for leaf, uks in leaf_groups.items():
        if len(uks) < 2:
            continue
        fps = {unit_meta[u]["fingerprint"] for u in uks}
        if len(fps) == 1:
            continue
        # if file counts equal and every basename hash matches, unify fp
        def basenames(u: str) -> dict[str, str]:
            meta = unit_meta[u]
            out = {}
            unit_dir = u.split("/", 1)[1]
            for f in meta["files"]:
                if Path(f).suffix.lower() in RESOURCE_EXTS:
                    continue
                within = f[len(unit_dir) :].lstrip("/") if f.startswith(unit_dir) else Path(f).name
                p = LEGACY / meta["repo"] / f
                if p.is_file():
                    out[within] = norm_content_hash(p)[0]
            return out

        maps = {u: basenames(u) for u in uks}
        keys0 = maps[uks[0]]
        if all(maps[u] == keys0 for u in uks[1:]):
            canon_fp = unit_meta[uks[0]]["fingerprint"]
            for u in uks[1:]:
                unit_meta[u]["fingerprint"] = canon_fp

    # cluster by fingerprint
    by_fp: dict[str, list[str]] = defaultdict(list)
    for uk, meta in unit_meta.items():
        by_fp[meta["fingerprint"]].append(uk)

    manifests = []
    covered: set[tuple[str, str]] = set()
    used_units: set[str] = set()

    def mark_covered(repo: str, files: list[str]):
        for f in files:
            covered.add((repo, f))

    # process fingerprint clusters
    for fp, uks in sorted(by_fp.items(), key=lambda x: (-len(x[1]), x[0])):
        # prefer Qt5 > Linux/QT > else; more files; newer latest commit
        uks_sorted = sorted(
            uks,
            key=lambda u: (
                0 if u.startswith("Qt5/") else 1 if u.startswith("Linux/QT/") else 2,
                -unit_meta[u]["file_count"],
                # negate ISO date via reverse lexicographic pad
                tuple(-ord(c) for c in (unit_meta[u]["latest"] or "0000-00-00")),
                u,
            ),
        )
        canonical_uk = uks_sorted[0]
        dup_uks = uks_sorted[1:]
        meta = unit_meta[canonical_uk]
        repo = meta["repo"]
        files = meta["files"]
        unit_path = canonical_uk  # already repo/...
        # earliest first_commit across the clone set
        first_dates = [
            unit_meta[u]["first"]
            for u in uks_sorted
            if unit_meta[u].get("first") and unit_meta[u]["first"] != "unknown"
        ]
        if first_dates:
            meta = dict(meta)
            meta["first"] = min(first_dates)

        # skip pure junk/meta aggregators that are empty of code — handle below
        tp = detect_third_party(unit_path, files, repo)
        leaf = unit_path.split("/")[-1]

        # CGI: not Qt — drop-junk / out of scope note
        if unit_path.startswith("Practice/CGI"):
            entry = {
                "unit": slugify(unit_path),
                "title": f"CGI（非 Qt）{leaf}",
                "target": "programming/qt",
                "verdict": "drop-junk",
                "canonical": [unit_path.replace(f"{repo}/", f"{repo}/", 1) if False else f"{repo}/" + "/".join(Path(files[0]).parts[:2]) if files else unit_path],
                "duplicates": [u for u in dup_uks],
                "first_commit": meta["first"] or "unknown",
                "files": meta["file_count"],
                "run": "read-only",
                "build": "n/a — CGI, not Qt",
                "build_checked": False,
                "topic_hint": "out-of-scope",
                "quality_notes": "Practice/CGI 与 Qt 无关，不归本清单入库",
                "reason": "任务书：Practice/CGI 若与 Qt 无关则不归 Qt 领域；显式 drop 以满足零遗漏",
                "_all_files": [(repo, f) for f in files],
            }
            # fix canonical path form: repo/rel_dir
            entry["canonical"] = [canonical_uk]
            manifests.append(entry)
            used_units.add(canonical_uk)
            used_units.update(dup_uks)
            mark_covered(repo, files)
            for du in dup_uks:
                mark_covered(unit_meta[du]["repo"], unit_meta[du]["files"])
            continue

        # root meta / gitignore
        if "/__root__/" in unit_path or unit_path.endswith("/__meta__"):
            entry = {
                "unit": slugify(unit_path),
                "title": f"元数据 {leaf}",
                "target": "programming/qt",
                "verdict": "drop-junk",
                "canonical": [canonical_uk],
                "duplicates": list(dup_uks),
                "first_commit": meta["first"] or "unknown",
                "files": meta["file_count"],
                "run": "read-only",
                "build": "n/a",
                "build_checked": False,
                "topic_hint": "n/a",
                "quality_notes": "仓库级 .pro / .gitignore / Sample 汇总工程文件",
                "reason": "非子工程练习单元，属容器元数据",
                "_all_files": [(repo, f) for f in files],
            }
            manifests.append(entry)
            used_units.add(canonical_uk)
            used_units.update(dup_uks)
            mark_covered(repo, files)
            for du in dup_uks:
                mark_covered(unit_meta[du]["repo"], unit_meta[du]["files"])
            continue

        if tp and ("Sample" in unit_path or "chap" in unit_path):
            # book samples: drop-third-party unless user-modified
            # detect user modification: compare Qt5 vs Linux — if identical, pure copy
            user_mod = False
            # heuristic: files with Chinese comments that look personal, or .user already junked
            for f in files:
                if f.endswith((".cpp", ".h", ".qml")):
                    head = read_head(LEGACY / repo / f)
                    if re.search(r"我的|练习笔记|修改于|FIXME\(me\)", head):
                        user_mod = True
                        break
            if not user_mod:
                verdict = "drop-third-party"
                reason = tp + "；与 Linux/Sample 或 Qt5/Sample 对照为整套拷贝，未见使用者改动痕迹"
            else:
                verdict = "keep"
                reason = tp + "；检测到疑似个人改动，保留待 leader 裁决"
            entry = {
                "unit": slugify(unit_path),
                "title": f"教材样例 {leaf}",
                "target": "programming/qt",
                "verdict": verdict,
                "canonical": [canonical_uk],
                "duplicates": list(dup_uks),
                "first_commit": meta["first"] or "unknown",
                "files": meta["file_count"],
                "run": "toolchain",
                "build": pick_build_cmd(repo, unit_path, files),
                "build_checked": False,
                "topic_hint": topic_hint_for(unit_path, leaf),
                "quality_notes": quality_notes_for(repo, unit_path, files),
                "reason": reason,
                "_all_files": [(repo, f) for f in files],
            }
            manifests.append(entry)
            used_units.add(canonical_uk)
            used_units.update(dup_uks)
            mark_covered(repo, files)
            for du in dup_uks:
                mark_covered(unit_meta[du]["repo"], unit_meta[du]["files"])
            continue

        if tp and ("QtAwesome" in tp or "qdarkstyle" in tp.lower()):
            entry = {
                "unit": slugify(unit_path),
                "title": leaf,
                "target": "programming/qt",
                "verdict": "drop-third-party",
                "canonical": [canonical_uk],
                "duplicates": list(dup_uks),
                "first_commit": meta["first"] or "unknown",
                "files": meta["file_count"],
                "run": "toolchain",
                "build": pick_build_cmd(repo, unit_path, files),
                "build_checked": False,
                "topic_hint": topic_hint_for(unit_path, leaf),
                "quality_notes": quality_notes_for(repo, unit_path, files),
                "reason": tp
                + (
                    "; upstream https://github.com/ColinDuquesnoy/QDarkStyleSheet"
                    if "qdarkstyle" in tp.lower()
                    else ""
                ),
                "_all_files": [(repo, f) for f in files],
            }
            manifests.append(entry)
            used_units.add(canonical_uk)
            used_units.update(dup_uks)
            mark_covered(repo, files)
            for du in dup_uks:
                mark_covered(unit_meta[du]["repo"], unit_meta[du]["files"])
            continue

        # normal keep / merge
        if dup_uks:
            verdict = "keep"
            # duplicates get separate drop-duplicate entries? README says duplicates field on canonical
            # Also need every file covered — dups covered via marking
            reason = ""
        else:
            verdict = "keep"
            reason = ""

        # orphan resource-only units
        codeish = [
            f
            for f in files
            if Path(f).suffix.lower()
            in {".cpp", ".h", ".hpp", ".c", ".qml", ".ui", ".pro", ".py", ".qrc", ".js"}
            or Path(f).name == "CMakeLists.txt"
        ]
        if not codeish:
            entry = {
                "unit": slugify(unit_path),
                "title": f"孤立资源 {leaf}",
                "target": "programming/qt",
                "verdict": "drop-junk",
                "canonical": [canonical_uk],
                "duplicates": list(dup_uks),
                "first_commit": meta["first"] or "unknown",
                "files": meta["file_count"],
                "run": "read-only",
                "build": "n/a",
                "build_checked": False,
                "topic_hint": "n/a",
                "quality_notes": "无源码，仅有位图/二进制",
                "reason": "孤立二进制资源，条目不依赖则 drop-junk",
                "_all_files": [(repo, f) for f in files],
            }
            manifests.append(entry)
            used_units.add(canonical_uk)
            used_units.update(dup_uks)
            mark_covered(repo, files)
            for du in dup_uks:
                mark_covered(unit_meta[du]["repo"], unit_meta[du]["files"])
            continue

        run = "toolchain"
        if any(f.endswith(".py") for f in files) and not any(
            f.endswith((".cpp", ".pro", ".qml")) for f in files
        ):
            run = "toolchain"

        entry = {
            "unit": slugify(unit_path),
            "title": unit_title(unit_path),
            "target": "programming/qt",
            "verdict": verdict,
            "canonical": [canonical_uk],
            "duplicates": list(dup_uks),
            "first_commit": meta["first"] or "unknown",
            "files": meta["file_count"],
            "run": run,
            "build": pick_build_cmd(repo, unit_path, files),
            "build_checked": False,
            "topic_hint": topic_hint_for(unit_path, leaf),
            "quality_notes": quality_notes_for(repo, unit_path, files),
            "reason": reason
            or (
                f"内容哈希相同，规范版取文件更多/更新者；重复于 {', '.join(dup_uks)}"
                if dup_uks
                else ""
            ),
            "_all_files": [(repo, f) for f in files],
        }
        manifests.append(entry)
        used_units.add(canonical_uk)
        used_units.update(dup_uks)
        mark_covered(repo, files)
        for du in dup_uks:
            mark_covered(unit_meta[du]["repo"], unit_meta[du]["files"])

    # junk files as aggregate drop units per top folder
    junk_by_bucket: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for repo, rel in junk_files:
        bucket = f"{repo}/{'/'.join(rel.split('/')[:2])}"
        junk_by_bucket[bucket].append((repo, rel))

    for bucket, pairs in sorted(junk_by_bucket.items()):
        manifests.append(
            {
                "unit": "junk-" + slugify(bucket),
                "title": f"构建/IDE 垃圾 {bucket}",
                "target": "programming/qt",
                "verdict": "drop-junk",
                "canonical": [bucket],
                "duplicates": [],
                "first_commit": "n/a",
                "files": len(pairs),
                "run": "read-only",
                "build": "n/a",
                "build_checked": False,
                "topic_hint": "n/a",
                "quality_notes": ".pro.user / 构建输出等",
                "reason": "IDE/构建生成物，任务书要求 drop-junk",
                "_all_files": pairs,
            }
        )
        for repo, rel in pairs:
            covered.add((repo, rel))

    # ensure unique unit ids
    seen_ids: dict[str, int] = {}
    for e in manifests:
        base = e["unit"]
        if base in seen_ids:
            seen_ids[base] += 1
            e["unit"] = f"{base}-{seen_ids[base]}"
        else:
            seen_ids[base] = 0

    # coverage check
    all_scoped = set(scoped)
    missing = sorted(all_scoped - covered)
    extra = sorted(covered - all_scoped)

    # write verify
    verify_lines = [
        f"generated: {datetime.now().isoformat(timespec='seconds')}",
        f"scoped_files: {len(all_scoped)}",
        f"covered_files: {len(covered & all_scoped)}",
        f"missing_files: {len(missing)}",
        f"extra_marks: {len(extra)}",
        f"units: {len(manifests)}",
        f"keep: {sum(1 for e in manifests if e['verdict']=='keep')}",
        f"drop-duplicate-via-field: {sum(1 for e in manifests if e['duplicates'])}",
        f"drop-third-party: {sum(1 for e in manifests if e['verdict']=='drop-third-party')}",
        f"drop-junk: {sum(1 for e in manifests if e['verdict']=='drop-junk')}",
        "",
        "=== missing (first 50) ===",
    ]
    for repo, rel in missing[:50]:
        verify_lines.append(f"  {repo}/{rel}")
    if len(missing) > 50:
        verify_lines.append(f"  ... +{len(missing)-50} more")

    (OUT_DIR / "verify-qt.txt").write_text("\n".join(verify_lines) + "\n", encoding="utf-8")

    # strip private fields for JSON
    public = []
    for e in manifests:
        pe = {k: v for k, v in e.items() if not k.startswith("_")}
        if not pe.get("reason"):
            pe.pop("reason", None)
        public.append(pe)

    # sort: keep first, then by topic_hint, unit
    def sort_key(e):
        order = {"keep": 0, "merge-into": 1, "drop-duplicate": 2, "drop-third-party": 3, "drop-junk": 4}
        v = e["verdict"]
        o = 1 if v.startswith("merge-into") else order.get(v, 9)
        return (o, e.get("topic_hint", ""), e["unit"])

    public.sort(key=sort_key)

    (OUT_DIR / "manifest-qt.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # also write a sidecars file mapping unit→files for build tester / coverage
    file_map = {
        e["unit"]: [f"{r}/{p}" for r, p in e.get("_all_files", [])] for e in manifests
    }
    # include duplicate unit files
    for e in manifests:
        for du in e.get("duplicates") or []:
            if du in unit_meta:
                file_map.setdefault(e["unit"] + "::dup::" + du, [
                    f"{unit_meta[du]['repo']}/{p}" for p in unit_meta[du]["files"]
                ])

    (OUT_DIR / "_qt_unit_files.json").write_text(
        json.dumps(
            {
                "missing": [f"{r}/{p}" for r, p in missing],
                "unit_files": {
                    e["unit"]: [f"{r}/{p}" for r, p in e["_all_files"]] for e in manifests
                },
                "dup_unit_files": {
                    du: [f"{unit_meta[du]['repo']}/{p}" for p in unit_meta[du]["files"]]
                    for e in manifests
                    for du in e.get("duplicates") or []
                    if du in unit_meta
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote {OUT_DIR / 'manifest-qt.json'} ({len(public)} units)")
    print(f"missing coverage: {len(missing)}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
