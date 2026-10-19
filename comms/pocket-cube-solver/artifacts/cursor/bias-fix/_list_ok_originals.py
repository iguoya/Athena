#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cp", HERE / "check_patch.py")
cp = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(cp)
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
PAREN = re.compile(r"（[^）]*）")


def ul(ch, a):
    L = len(ch[a])
    return all(len(c) < L for i, c in enumerate(ch) if i != a)


for app in ("snake", "chinese-chess", "c-plus-plus"):
    orig = cp.load_original(app)
    print(f"\n=== {app} ===")
    for qid, q in sorted(orig.items()):
        ok_len = cp.length_ok(q["choices"], q["answer"])
        paren = any(PAREN.search(c) for c in q["choices"])
        flag = "KEEP" if ok_len and not paren else "REWRITE"
        u = "UL" if ul(q["choices"], q["answer"]) else "-"
        print(f"  {flag} [{u}] {qid}")
