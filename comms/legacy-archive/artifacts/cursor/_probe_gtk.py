import json
from collections import Counter
from pathlib import Path

for name in ["gtk", "gtkmm"]:
    d = json.load(open(f"comms/legacy-archive/artifacts/cursor/manifest-{name}.json", encoding="utf-8"))
    print("===", name, len(d), Counter(e["verdict"] for e in d))
    print(" keep ver", Counter(e.get("gtk_version") for e in d if e["verdict"] == "keep"))
    print(" keep topic", Counter(e["topic_hint"] for e in d if e["verdict"] == "keep"))
    print(" with dups", sum(1 for e in d if e.get("duplicates")))
    print(" junk files total", sum(e["files"] for e in d if e["verdict"] == "drop-junk"))

root = Path(".cache/legacy-src/Linux")
for rel in [
    "GTK/g19-basicwindow/src/main.c",
    "GTK/g20-box/src/main.c",
    "GTK/GtkApp/src/main.c",
    "GTK/25-glade/src/main.c",
    "GTKMM/1-Hello/main.cpp",
    "GTKMM/2-glade/src/main.cc",
    "GTKMM/6-box/src/main.cc",
]:
    p = root / rel
    print("---", rel, "exists", p.exists())
    if not p.exists():
        # find alternatives
        parent = root / Path(rel).parts[0] / Path(rel).parts[1]
        if parent.is_dir():
            for q in parent.rglob("*"):
                if q.suffix in {".c", ".cpp", ".cc"} and q.name.startswith("main"):
                    print(" alt", q.relative_to(root))
                    p = q
                    break
    if p.exists():
        t = p.read_text(encoding="utf-8", errors="ignore")
        print(t[:450])
        print("markers:", 
              "gtk_hbox" in t, 
              "GtkApplication" in t, 
              "gtk_init" in t, 
              "gtkmm" in t.lower(),
              "Gtk::" in t)
