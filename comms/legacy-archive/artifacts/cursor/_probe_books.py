#!/usr/bin/env python3
from pathlib import Path
import re

root = Path(".cache/legacy-src")

for label, base in [
    ("QmlBook", root / "Practice" / "QT" / "QmlBook"),
    ("Qt5开发及实例", root / "Practice" / "QT" / "Qt5开发及实例"),
    ("untitled", root / "Practice" / "untitled"),
]:
    print(f"\n==== {label} ====")
    if not base.exists():
        print("MISSING")
        continue
    files = [p for p in base.rglob("*") if p.is_file()]
    print("files", len(files))
    for p in files[:30]:
        print(" ", p.relative_to(base))
    # copyright / license / readme
    for p in files:
        name = p.name.lower()
        if any(x in name for x in ("readme", "license", "copying", "authors", "notice")):
            print("DOC", p.relative_to(base))
            print(p.read_text(encoding="utf-8", errors="ignore")[:500])
    # scan headers
    hits = 0
    for p in files:
        if p.suffix.lower() not in {".cpp", ".h", ".qml", ".js", ".md", ".txt", ".py"}:
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")[:2500]
        if re.search(
            r"(?i)copyright|license|all rights|creativecommons|MIT\b|BSD|王英|清华|电子工业|qmlbook|qt\.io",
            t,
        ):
            print("HIT", p.relative_to(base))
            print(t[:400].replace("\r", ""))
            print("---")
            hits += 1
            if hits >= 6:
                break
    print("header hits", hits)
