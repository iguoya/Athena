#!/usr/bin/env python3
"""对五处设计模式源码做规范化内容哈希去重（T-001 证据脚本）。

规范化规则：统一行尾为 LF、去掉每行行尾空白、去掉文件首尾空白行后取 SHA-256。
二进制文件按原始字节哈希。输出按簇聚合的重复报告。
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(".cache/legacy-src")

# 五处范围（仓库, 仓库内路径前缀）；None 表示整个仓库
SCOPES = [
    ("DesignPattern", None),
    ("DesignPatterns", None),
    ("Practice", "DesignPatterns"),
    ("Linux", "DesignPattern"),
    ("Linux", "DesignEvolutionCpp"),
    ("algorithm", "design-patterns"),
]

TEXT_EXT = {".cpp", ".h", ".c", ".md", ".txt", ".pro", ".qrc", ".ui", ".json",
            ".sh", ".yml", ".yaml", ".js", ".py", ".rst", ".mk", ".in", ".bat",
            ".xmi", ".plist", ".pbxproj", ".workspacedata", ".lck", ".mdj",
            ".gitignore", ".project", ".schemes", ".user"}
BIN_HINT = {".zip", ".pdf", ".png", ".jpg", ".svgz", ".pickle", ".pyc", ".bmp",
            ".ico", ".gif", ".exe", "", ".bin"}


def norm_hash(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def raw_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    clusters: dict[str, list[str]] = {}
    for repo, prefix in SCOPES:
        out = subprocess.run(
            ["git", "-C", str(ROOT / repo), "ls-files", "-z"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        ).stdout
        for rel in out.split("\0"):
            if not rel or (prefix and not rel.startswith(prefix + "/")):
                continue
            p = ROOT / repo / rel
            try:
                data = p.read_bytes()
            except OSError as e:
                print(f"WARN 无法读取 {repo}/{rel}: {e}", file=sys.stderr)
                continue
            ext = Path(rel).suffix.lower()
            if ext in TEXT_EXT:
                h = "T:" + norm_hash(data)
            else:
                h = "R:" + raw_hash(data)
            clusters.setdefault(h, []).append(f"{repo}/{rel}")

    dup_count = 0
    for h, paths in sorted(clusters.items(), key=lambda kv: kv[1][0]):
        if len(paths) > 1:
            dup_count += 1
            print(f"=== 簇 {h[:12]}（{len(paths)} 份）===")
            for p in sorted(paths):
                print(f"  {p}")
    total_files = sum(len(v) for v in clusters.values())
    uniq = len(clusters)
    print(f"\n合计文件 {total_files}，唯一内容 {uniq}，多份簇 {dup_count}")


if __name__ == "__main__":
    main()
