#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bp", HERE / "build_patches.py")
bp = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bp)
spec2 = importlib.util.spec_from_file_location("cp", HERE / "check_patch.py")
cp = importlib.util.module_from_spec(spec2)
assert spec2.loader is not None
spec2.loader.exec_module(cp)
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


def ul(ch, a):
    L = len(ch[a])
    return all(len(c) < L for i, c in enumerate(ch) if i != a)


def dump(name, items):
    print(f"\n=== {name} ===")
    for it in items:
        ch, a = it["choices"], it["answer"]
        lengths = [len(c) for c in ch]
        flag = "UL" if ul(ch, a) else ("TIE" if lengths[a] == max(lengths) else "ok")
        bad = "" if cp.length_ok(ch, a) else " BADLEN"
        print(f"  [{flag}]{bad} {it['id']}: {lengths} ans={a} L={lengths[a]}")


dump("snake", bp.SNAKE)
dump("chess", bp.CHESS)
dump("cpp", bp.CPP)
