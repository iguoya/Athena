# -*- coding: utf-8 -*-
"""Score hand-written GTK logic (exclude Anjuta boilerplate files)."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SRC = REPO / ".cache" / "legacy-src" / "Linux" / "GTK"

# Anjuta / GNOME Builder style generated names
BOILER = re.compile(
    r"(application\.(c|h)|window\.(c|h)|resources\.c|"
    r".*-application\.(c|h)|.*-window\.(c|h)|main\.c)$",
    re.I,
)
# Still count main.c if it's the only source and has callbacks
INTERESTING = re.compile(
    r"g_signal_connect|gtk_box_pack|GtkHBox|GtkVBox|gtk_table_|"
    r"gtk_grid_|gtk_builder_|gtk_css_|GtkApplication|"
    r"gtk_widget_show_all|gtk_main\(|g_application_run",
)


def score_unit(rel: str) -> dict:
    root = SRC.parent.parent / rel if not rel.startswith("Linux") else REPO / ".cache" / "legacy-src" / rel
    # fix
    root = REPO / ".cache" / "legacy-src" / rel
    if not root.exists():
        return {"rel": rel, "error": "missing"}
    hand = []
    boiler = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".c", ".cpp", ".h", ".hpp", ".cc"}:
            continue
        if any(x in p.parts for x in ("build", "CMakeFiles", ".git")):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("/*")]
        loc = len(lines)
        rp = p.relative_to(root).as_posix()
        name = p.name
        is_boiler = bool(
            re.search(r"-application\.(c|h)$|-window\.(c|h)$|^resources\.c$", name, re.I)
        )
        # gnome builder templates often have identical application.c
        if "TODO: Add private" in text or "G_DEFINE_TYPE" in text and loc > 80 and "activate" in text:
            if name.endswith("-application.c") or name.endswith("application.c"):
                is_boiler = True
        signals = len(re.findall(r"g_signal_connect", text))
        callbacks = len(re.findall(r"static\s+void\s+\w+\s*\(", text))
        interesting = bool(INTERESTING.search(text))
        entry = {
            "file": rp,
            "loc": loc,
            "signals": signals,
            "callbacks": callbacks,
            "interesting": interesting,
            "boiler": is_boiler,
        }
        if is_boiler:
            boiler.append(entry)
        else:
            hand.append(entry)
    hand_loc = sum(x["loc"] for x in hand)
    hand_sig = sum(x["signals"] for x in hand)
    return {
        "rel": rel,
        "hand_loc": hand_loc,
        "hand_signals": hand_sig,
        "hand_files": hand,
        "boiler_files": len(boiler),
    }


def main() -> None:
    import json

    m = json.loads(
        (REPO / "comms/legacy-archive/artifacts/cursor/manifest-gtk.json").read_text(
            encoding="utf-8"
        )
    )
    rows = []
    for x in m:
        if x.get("verdict") != "keep":
            continue
        s = score_unit(x["canonical"][0])
        s["unit"] = x["unit"]
        rows.append(s)
    rows.sort(key=lambda r: (-r.get("hand_loc", 0), -r.get("hand_signals", 0)))
    print("unit | hand_loc | signals | hand files")
    for r in rows:
        if "error" in r:
            print(r)
            continue
        files = ", ".join(f"{f['file']}({f['loc']})" for f in r["hand_files"][:6])
        print(f"{r['unit']:28} loc={r['hand_loc']:4} sig={r['hand_signals']:3} | {files}")

    print("\n=== GTKMM ===")
    for rel in [
        "Linux/GTKMM/1-Hello",
        "Linux/GTKMM/2-glade",
        "Linux/GTKMM/3-frame",
        "Linux/GTKMM/4-paned",
        "Linux/GTKMM/5-asspectframe",
        "Linux/GTKMM/6-box",
        "Linux/GTKMM/7-box",
        "Linux/DesignEvolutionCpp",
    ]:
        root = REPO / ".cache" / "legacy-src" / rel
        print(f"\n## {rel}")
        for p in sorted(root.rglob("*")):
            if p.suffix.lower() in {".cpp", ".h", ".c", ".cc"} and p.is_file():
                if any(x in p.parts for x in ("build", "CMakeFiles")):
                    continue
                text = p.read_text(encoding="utf-8", errors="replace")
                print(f"--- {p.relative_to(root).as_posix()} ({len(text.splitlines())} lines) ---")
                print(text[:2500])
                if len(text) > 2500:
                    print("...[truncated]...")


if __name__ == "__main__":
    main()
