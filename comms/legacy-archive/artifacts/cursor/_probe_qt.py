#!/usr/bin/env python3
from pathlib import Path
import subprocess
import collections
import hashlib

root = Path(".cache/legacy-src")


def norm_hash(p: Path):
    data = p.read_bytes()
    if b"\0" in data[:4096]:
        return hashlib.sha256(data).hexdigest()
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            t = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return hashlib.sha256(data).hexdigest()
    t = t.replace("\r\n", "\n").replace("\r", "\n").strip()
    return hashlib.sha256(t.encode()).hexdigest()


# Compare Qt5/01-SignalSlot vs Linux/QT/01-SignalSlot
for name in ["01-SignalSlot", "20-SignalAndSlot", "11-HelloWorld"]:
    a = sorted((root / "Qt5" / name).rglob("*"))
    b = sorted((root / "Linux" / "QT" / name).rglob("*"))
    a = [p for p in a if p.is_file() and ".pro.user" not in p.name]
    b = [p for p in b if p.is_file() and ".pro.user" not in p.name]
    print(f"\n=== {name} Qt5={len(a)} Linux={len(b)} ===")
    amap = {p.relative_to(root / "Qt5" / name).as_posix(): norm_hash(p) for p in a}
    bmap = {p.relative_to(root / "Linux" / "QT" / name).as_posix(): norm_hash(p) for p in b}
    keys = sorted(set(amap) | set(bmap))
    same = sum(1 for k in keys if amap.get(k) == bmap.get(k))
    print(f"  path-aligned same hashes: {same}/{len(keys)}")
    for k in keys:
        if amap.get(k) != bmap.get(k):
            print(f"  DIFF {k}: qt5={amap.get(k,'')[:8]} lin={bmap.get(k,'')[:8]}")

# first commit probe
for repo, path in [
    ("Linux", "QT/01-SignalSlot/main.cpp"),
    ("Qt5", "01-SignalSlot/main.cpp"),
    ("Linux", "Sample/chap01Introduction/samp1_1Hello/main.cpp"),
]:
    out = subprocess.run(
        ["git", "-C", str(root / repo), "log", "--follow", "--format=%ad", "--date=short", "--diff-filter=A", "--", path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(f"\nfirst {repo}/{path}: rc={out.returncode} out={out.stdout.strip()!r} err={out.stderr.strip()[:200]!r}")

# Sample README / book markers
for p in (root / "Linux" / "Sample").rglob("*"):
    if p.suffix.lower() in {".txt", ".md", ".pdf"} or "readme" in p.name.lower():
        print("DOC", p.relative_to(root))

# QmlBook
qb = root / "Practice" / "QT"
if qb.exists():
    for child in qb.iterdir():
        print("Practice/QT child:", child.name)

# hunt book string in Sample
hits = 0
for p in (root / "Linux" / "Sample").rglob("*"):
    if p.suffix.lower() not in {".cpp", ".h", ".pro", ".ui", ".txt", ".md"}:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")[:2000]
    except OSError:
        continue
    if any(k in t for k in ("王英", "清华", "电子工业", "ISBN", "Qt5.9", "Qt 5.9", "配套")):
        print("BOOKHIT", p.relative_to(root))
        print(t[:350])
        hits += 1
        if hits >= 8:
            break
print("book hits", hits)

# QtApp structure
files = subprocess.check_output(
    ["git", "-C", str(root / "Linux"), "ls-files", "QT/QtApp"],
    text=True,
    encoding="utf-8",
).splitlines()
c = collections.Counter()
for f in files:
    parts = f.split("/")
    if len(parts) >= 3:
        c[parts[2]] += 1
print("\nQtApp children", len(c))
for k, v in c.most_common(20):
    print(f"  {k}: {v}")
