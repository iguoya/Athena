#!/usr/bin/env python3
"""T-002 哈希去重：algorithm / Practice/DataStructure / Linux/Algorithm。

规范化同 dedup.py（统一 LF、去行尾空白、去首尾空行后 SHA-256）。输出多份簇报告。
"""
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(".cache/legacy-src")
SCOPES = [
    ("algorithm", None),          # 整仓库；design-patterns/、docs/ 归 T-001，输出时过滤
    ("Practice", "DataStructure"),
    ("Linux", "Algorithm"),
]
TEXT_EXT = {".cpp", ".h", ".c", ".md", ".txt", ".sh", ".yml", ".json", ".js", ".py",
            ".qrc", ".ui", ".ts", ".css", ".cmake", ".user", ".bc", ".ll", ".rst"}

def norm_hash(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "T:" + hashlib.sha256("\n".join(lines).encode()).hexdigest()

def raw_hash(data: bytes) -> str:
    return "R:" + hashlib.sha256(data).hexdigest()

def main() -> None:
    clusters: dict[str, list[str]] = {}
    for repo, prefix in SCOPES:
        out = subprocess.run(["git", "-C", str(ROOT / repo), "ls-files", "-z"],
                             capture_output=True).stdout
        for raw in out.split(b"\0"):
            if not raw:
                continue
            rel = raw.decode("utf-8")
            if repo == "algorithm" and (rel.startswith("design-patterns/") or rel.startswith("docs/")):
                continue  # 归 T-001
            if prefix and not rel.startswith(prefix + "/"):
                continue
            data = (ROOT / repo / rel).read_bytes()
            ext = Path(rel).suffix.lower()
            h = norm_hash(data) if ext in TEXT_EXT else raw_hash(data)
            clusters.setdefault(h, []).append(f"{repo}/{rel}")

    for h, paths in sorted(clusters.items(), key=lambda kv: kv[1][0]):
        if len(paths) > 1:
            print(f"=== 簇 {h[:14]}（{len(paths)} 份）===")
            for p in sorted(paths):
                print(f"  {p}")
    total = sum(len(v) for v in clusters.values())
    print(f"\n合计文件 {total}，唯一内容 {len(clusters)}，多份簇 "
          f"{sum(1 for v in clusters.values() if len(v) > 1)}")

if __name__ == "__main__":
    main()
