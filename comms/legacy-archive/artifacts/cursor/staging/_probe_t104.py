# -*- coding: utf-8 -*-
"""Probe gtkmm / gtk sources for T-104 selection."""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SRC = REPO / ".cache" / "legacy-src"
ART = REPO / "comms" / "legacy-archive" / "artifacts" / "cursor"


def dump_keeps(name: str) -> list[dict]:
    m = json.loads((ART / f"manifest-{name}.json").read_text(encoding="utf-8"))
    keeps = [x for x in m if x.get("verdict") == "keep"]
    print(f"=== {name} keep={len(keeps)} ===")
    for x in keeps:
        q = (x.get("quality_notes") or "")[:100]
        print(
            f"{x['unit']:30} files={x.get('files'):3} "
            f"run={x.get('run'):10} first={x.get('first_commit')} | {q}"
        )
    return keeps


def list_tree(rel: str, max_files: int = 40) -> None:
    p = SRC / rel
    print(f"\n--- {rel} exists={p.is_dir()} ---")
    if not p.is_dir():
        return
    n = 0
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in {".git", "build", "Debug", "Release", "CMakeFiles"}]
        for f in files:
            rp = Path(root, f).relative_to(p).as_posix()
            print(rp)
            n += 1
            if n >= max_files:
                print("...")
                return


def count_loc(rel: str) -> tuple[int, list[str]]:
    """Rough LOC of .c/.cpp/.h/.cc hand-written sources."""
    p = SRC / rel
    total = 0
    sources: list[str] = []
    if not p.is_dir():
        return 0, []
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in {".git", "build", "Debug", "Release", "CMakeFiles"}]
        for f in files:
            if not f.endswith((".c", ".cpp", ".cc", ".h", ".hpp", ".cxx")):
                continue
            fp = Path(root) / f
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # skip pure glade-generated stubs that are tiny
            lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("//")]
            total += len(lines)
            sources.append(f"{fp.relative_to(p).as_posix()}:{len(lines)}")
    return total, sources


def main() -> None:
    dump_keeps("gtkmm")
    list_tree("Linux/GTKMM")
    list_tree("Linux/DesignEvolutionCpp")
    # first_commit for DesignEvolutionCpp
    import subprocess

    r = subprocess.run(
        [
            "git",
            "-C",
            str(SRC / "Linux"),
            "log",
            "--follow",
            "--format=%ad",
            "--date=short",
            "--diff-filter=A",
            "--",
            "DesignEvolutionCpp",
        ],
        capture_output=True,
        text=True,
    )
    dates = [ln for ln in r.stdout.splitlines() if ln.strip()]
    print("DesignEvolutionCpp first_commit candidates:", dates[-1:] if dates else "NONE", "count", len(dates))

    keeps = dump_keeps("gtk")
    print("\n=== LOC scan for gtk keep ===")
    rows = []
    for x in keeps:
        can = x["canonical"][0]
        # strip Linux/ prefix? canonical is like Linux/GTK/...
        loc, srcs = count_loc(can)
        rows.append((loc, x["unit"], can, srcs[:5]))
    rows.sort(reverse=True)
    for loc, unit, can, srcs in rows:
        print(f"{loc:5} {unit:30} {can}")
        for s in srcs:
            print(f"      {s}")


if __name__ == "__main__":
    main()
