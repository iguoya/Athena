#!/usr/bin/env python3
import json
import runpy
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
runpy.run_path(str(HERE / "build_patches.py"), run_name="__main__")

for app in ("snake", "chinese-chess", "c-plus-plus"):
    patch = json.loads((HERE / f"{app}.json").read_text(encoding="utf-8"))
    for item in patch:
        ch = item["choices"]
        a = item["answer"]
        L = len(ch[a])
        for i, c in enumerate(ch):
            if i == a:
                continue
            if L and abs(len(c) - L) / L > 0.40:
                print(f"{app} {item['id']}")
                print(f"  [{a}] ({L}) {ch[a]}")
                print(f"  [{i}] ({len(c)}) {c}")
