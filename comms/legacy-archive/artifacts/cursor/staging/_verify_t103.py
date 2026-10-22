# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "scripts"))
import archive_check as a

app = Path(__file__).resolve().parent / "qt"
problems = a.check_app(app)
arc = json.loads((app / "content" / "archive.json").read_text(encoding="utf-8"))
topics = arc["chapters"][0]["topics"]
dropped = sum(
    1
    for l in (app / "content" / "archive-dropped.md").read_text(encoding="utf-8").splitlines()
    if l.startswith("- ")
)
cases = len(list((app / "content" / "cases").glob("arc_*")))
checked = sum(
    1
    for t in topics
    for b in t["lesson"]["blocks"]
    if b.get("type") == "archive" and "实测 Qt 6.8.1 通过" in b.get("summary", "")
)
lines = [
    f"archive_check: {'OK (0 problems)' if not problems else problems}",
    f"topics={len(topics)} drop-trivial={dropped} case_dirs={cases}",
    f"summaries_with_实测_Qt6.8.1={checked}",
    f"all_run=toolchain: {all(b.get('run')=='toolchain' for t in topics for b in t['lesson']['blocks'] if b.get('type')=='archive')}",
]
text = "\n".join(lines) + "\n"
out = Path(__file__).resolve().parent / "verify-t103.txt"
out.write_text(text, encoding="utf-8")
print(text)
if problems:
    raise SystemExit(1)
