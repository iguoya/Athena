#!/usr/bin/env python3
"""分析原文哪些题长度已合格、哪些需要手写等长干扰项或缩短正确项。"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cp", HERE / "check_patch.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


def main() -> None:
    for app in ("snake", "chinese-chess", "c-plus-plus"):
        orig = mod.load_original(app)
        print(f"\n=== {app} {len(orig)} ===")
        ok = need = 0
        for qid, q in sorted(orig.items()):
            ans = q["answer"]
            L = len(q["choices"][ans])
            ratios = [
                abs(len(c) - L) / L for i, c in enumerate(q["choices"]) if i != ans
            ]
            if all(r <= 0.40 for r in ratios):
                ok += 1
                continue
            need += 1
            print(f"\nSHORT {qid} correct_len={L}")
            print(f"  C[{ans}]: {q['choices'][ans]}")
            for i, c in enumerate(q["choices"]):
                if i == ans:
                    continue
                r = abs(len(c) - L) / L
                mark = " !" if r > 0.40 else ""
                print(f"  [{i}] len={len(c)} r={r:.0%}{mark}: {c}")
        print(f"\n  length-ok={ok} need-fix={need}")


if __name__ == "__main__":
    main()
