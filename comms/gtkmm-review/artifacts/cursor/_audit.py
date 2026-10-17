# T-001 只读对账脚本（本应 python 跑；本会话 Shell 钩子全灭，证据改由人工复核 + 本脚本待跑）
# 用法（仓库根）：python comms/gtkmm-review/artifacts/cursor/_audit.py
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # Athena
APP = ROOT / "guide" / "gtkmm"
CUR = json.loads((APP / "content" / "curriculum.json").read_text(encoding="utf-8"))
DEMOS = json.loads((APP / "content" / "demos.json").read_text(encoding="utf-8"))
UP = APP / "upstream" / "gtkmm-documentation" / "examples" / "book"
EX = APP / "exercise"

FIRST10 = [s for s in CUR["sections"] if s.get("order") in range(1, 11)]
PAGE_IDS = {p["id"] for s in FIRST10 for p in s.get("pages", [])}
KP_IDS = {kp["id"] for s in FIRST10 for kp in s.get("knowledge_points", [])}


def file_sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def walk_files(base: Path) -> dict[str, Path]:
    out = {}
    if not base.is_dir():
        return out
    for p in base.rglob("*"):
        if p.is_file():
            out[p.relative_to(base).as_posix()] = p
    return out


print("=== chapters order 1-10 ===")
for s in FIRST10:
    print(f"  {s['order']:2d} {s['id']} pages={len(s.get('pages',[]))} kps={len(s.get('knowledge_points',[]))} status={s.get('status')}")

print("\n=== curriculum block types (order 1-10) ===")
from collections import Counter

types = Counter()
demo_refs = []
for s in FIRST10:
    for kp in s.get("knowledge_points", []):
        for b in kp.get("blocks", []):
            types[b.get("type")] += 1
            if "demo_ref" in b:
                demo_refs.append((s["id"], kp["id"], b["type"], b["demo_ref"]))
    for cp in s.get("checkpoint", []) or []:
        types["checkpoint:" + (cp.get("type") or "quiz")] += 1
print(dict(types))
print("demo_refs:", demo_refs)

print("\n=== demos/experiments/examples scoped to chapter 1-10 ===")
for kind in ("demos", "experiments", "examples"):
    for e in DEMOS.get(kind, []):
        ch = (e.get("translation_ref") or {}).get("chapter")
        if ch is None or not (1 <= int(ch) <= 10):
            continue
        pr = e.get("page_ref")
        dangling = pr and pr not in PAGE_IDS
        print(f"  {kind[:-1]} {e['id']} ch={ch} page_ref={pr!r} dangling={dangling}")
        for tr in e.get("theory_refs") or []:
            if tr not in KP_IDS:
                print(f"    theory_ref dangling: {tr}")

print("\n=== exercise vs upstream (chapter-relevant sets) ===")
# sets used by examples with translation_ref.chapter <= 10
sets = set()
for e in DEMOS.get("examples", []):
    ch = (e.get("translation_ref") or {}).get("chapter")
    if ch is not None and 1 <= int(ch) <= 10:
        # source_dir like exercise/buttons/button
        parts = Path(e["source_dir"]).parts  # exercise, set, name...
        if len(parts) >= 2 and parts[0] == "exercise":
            sets.add(parts[1])

print("sets:", sorted(sets))
print("upstream exists:", UP.is_dir())
mismatches = []
missing_up = []
missing_ex = []
extra_ex = []
for sname in sorted(sets):
    u = UP / sname
    x = EX / sname
    uf = walk_files(u)
    xf = walk_files(x)
    if not u.is_dir():
        missing_up.append(sname)
        continue
    if not x.is_dir():
        missing_ex.append(sname)
        continue
    for rel, up in uf.items():
        if rel not in xf:
            mismatches.append((sname, rel, "only-upstream"))
        elif file_sha(up) != file_sha(xf[rel]):
            mismatches.append((sname, rel, "content-diff"))
    for rel in xf:
        if rel not in uf:
            extra_ex.append((sname, rel))
print("missing_up_sets:", missing_up)
print("missing_ex_sets:", missing_ex)
print("content/only-up mismatches:", len(mismatches))
for m in mismatches[:30]:
    print(" ", m)
print("extra_ex files:", len(extra_ex))
for m in extra_ex[:30]:
    print(" ", m)

print("\n=== demo source line counts ===")
for e in DEMOS.get("demos", []):
    ch = (e.get("translation_ref") or {}).get("chapter")
    if ch is None or not (1 <= int(ch) <= 10):
        continue
    src = APP / e["source_dir"] / "src"
    lines = 0
    for p in src.rglob("*"):
        if p.suffix in {".cpp", ".cc", ".h", ".hpp", ".c"}:
            lines += len(p.read_text(encoding="utf-8", errors="replace").splitlines())
    flag = "OVER" if lines > 150 else "ok"
    print(f"  {e['id']} lines≈{lines} {flag} dir={e['source_dir']}")
