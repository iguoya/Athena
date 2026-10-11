#!/usr/bin/env python3
"""按 upstream.json 的钉点把官方教程源拉到 upstream/gtkmm-documentation（gitignore）。

check.py 用其中的 DocBook 核对课表结构与官方章节一致（extract_source.py），新机器与
CI 上要先有这份源，且必须是 upstream.json 钉住的那个提交——上游 master 一动，段落
指纹与章节结构就会对不上。钉点只在 upstream.json 一处（改它走「同步上游」流程，见
AGENTS.md），这里只读不写。

已存在的克隆不动（可能是使用者正在上面做同步），只在提交不符时提醒。

用法：
    python3 scripts/fetch_upstream.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET = PROJECT_ROOT / "upstream" / "gtkmm-documentation"


def head(git: str) -> str:
    return subprocess.run(
        [git, "-C", str(TARGET), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


def run(command: list[str]) -> None:
    if subprocess.run(command).returncode != 0:
        raise SystemExit(f"失败：{' '.join(command)}")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    pin = json.loads((PROJECT_ROOT / "upstream.json").read_text(encoding="utf-8"))
    url, commit, version = pin["url"], pin["pinned_commit"], pin.get("pinned_version")
    git = shutil.which("git")
    if git is None:
        raise SystemExit("找不到 git")

    if TARGET.is_dir():
        current = head(git)
        if current != commit:
            print(f"提示：{TARGET.relative_to(PROJECT_ROOT)} 在 {current[:7] or '未知提交'}，"
                  f"upstream.json 钉在 {commit[:7]}；不一致时 check 的结构核对可能报差异。")
        else:
            print(f"官方源已就绪：{version or ''}（{commit[:7]}）")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    # 钉点有版本标签就浅克隆标签（几 MB）；标签不在或不指向钉住的提交，退回完整克隆再签出。
    if version:
        print(f"克隆 {url} @ {version}", flush=True)
        run([git, "-c", "advice.detachedHead=false", "clone", "--quiet", "--depth", "1", "--branch", version, url, str(TARGET)])
        if head(git) == commit:
            print(f"官方源已就绪：{version}（{commit[:7]}）")
            return 0
        print(f"标签 {version} 不指向 {commit[:7]}，改为完整克隆后签出钉住的提交", flush=True)
        shutil.rmtree(TARGET)
    run([git, "clone", "--quiet", url, str(TARGET)])
    run([git, "-c", "advice.detachedHead=false", "-C", str(TARGET), "checkout", "--quiet", commit])
    print(f"官方源已就绪：{commit[:7]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
