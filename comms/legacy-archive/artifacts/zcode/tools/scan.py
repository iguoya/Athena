# -*- coding: utf-8 -*-
"""扫描 .cache/legacy-src/ 下我负责范围的被跟踪文件，算规范化内容哈希。

规范化：CRLF/LF 统一、每行行尾空白去掉、去掉文件末尾空行；行首缩进保留。
二进制文件按原始字节哈希。输出 scan.json 供去重与零遗漏校验共用。
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\tiger\Athena\.cache\legacy-src")
OUT = Path(r"C:\Users\tiger\Athena\comms\legacy-archive\artifacts\zcode\scan.json")

TEXT_EXTS = {
    ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hh", ".py", ".md", ".txt",
    ".pro", ".ui", ".qrc", ".qml", ".json", ".yml", ".yaml", ".toml", ".xml",
    ".css", ".js", ".ts", ".html", ".sh", ".mk", ".workspace", ".mdj",
    ".gitignore", ".rst", ".cfg", ".ts", ".glade", ".project", ".cproject",
    ".settings", ".user", ".stx", ".vue", ".scss", ".bat", ".cmake",
}


def norm_hash(data: bytes, ext: str) -> tuple[str, str]:
    """返回 (规范化哈希, 原始字节哈希)。"""
    raw = hashlib.sha256(data).hexdigest()
    if ext in TEXT_EXTS or (b"\x00" not in data[:4096] and data[:4096].isascii() is not None and b"\x00" not in data):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = data.decode("gbk")
            except UnicodeDecodeError:
                return raw, raw
        lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        while lines and lines[-1] == "":
            lines.pop()
        return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest(), raw
    return raw, raw


def main():
    # 我负责的 (仓库, 路径前缀) 规则；None = 全仓
    scope = {
        "DesignPattern": [None],
        "DesignPatterns": [None],
        "Practice": ["DesignPatterns/", "DataStructure/"],
        "Linux": ["DesignPattern/", "DesignEvolutionCpp/", "Algorithm/", "C/"],
        "algorithm": [None],
        "Qt5": [],
    }
    records = []
    for repo, prefixes in scope.items():
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "ls-files", "-z"],
            cwd=ROOT / repo, capture_output=True, check=True)
        files = out.stdout.decode("utf-8").split("\0")
        files = [f for f in files if f]
        for f in files:
            if prefixes is not None and not any(p is None or f.startswith(p) for p in prefixes):
                continue
            p = ROOT / repo / f
            try:
                data = p.read_bytes()
            except OSError as e:
                print(f"READ-FAIL {repo}/{f}: {e}", file=sys.stderr)
                continue
            ext = p.suffix.lower()
            nh, rh = norm_hash(data, ext)
            records.append({
                "repo": repo, "path": f, "norm": nh, "raw": rh,
                "size": len(data), "ext": ext,
            })
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"共 {len(records)} 个文件 -> {OUT}")


if __name__ == "__main__":
    main()
