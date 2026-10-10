#!/usr/bin/env python3
"""赛历应用的验证入口：赛事数据校验、前端构建、Rust 侧检查。

赛历是参考类应用，正确性靠数据纪律：每条资格要么有来源与核对日期，要么如实标
pending（ADR 0114）。这一条机器能查，就在这里查，别等界面上露馅。

用法：
    python3 scripts/check.py [--skip-rust]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA = PROJECT_ROOT / "content" / "competitions.json"
ALLOW = {"yes", "no", "per-event", "pending"}
LEVELS = {"official", "notice", "report", "pending"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8，打印中文会抛 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    # Windows 上 npm 实际是 npm.cmd，which 按 PATHEXT 查找才拿得到可执行路径（ADR 0047）。
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请先安装后重试")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def check_data() -> None:
    print("== 赛事数据校验 ==", flush=True)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    directions = {d["id"] for d in data["directions"]}
    problems: list[str] = []
    seen: set[str] = set()
    for c in data["competitions"]:
        cid = c.get("id", "?")
        where = f"competitions[{cid}]"
        if cid in seen:
            problems.append(f"{where}: id 重复")
        seen.add(cid)
        if c.get("direction") not in directions:
            problems.append(f"{where}: direction {c.get('direction')!r} 不在 directions 里")
        for key in ("students", "public"):
            if c.get(key) not in ALLOW:
                problems.append(f"{where}: {key} 只能是 {sorted(ALLOW)}")
        url = c.get("url")
        if url is not None and not url.startswith("https://"):
            problems.append(f"{where}: url 只收 https，确认不了就留 null")
        v = c.get("verify") or {}
        level = v.get("level")
        if level not in LEVELS:
            problems.append(f"{where}: verify.level 只能是 {sorted(LEVELS)}")
        elif level == "pending":
            # pending 就是「没查过」，带上来源或日期会让界面误显示成已核对。
            if v.get("source") or v.get("date"):
                problems.append(f"{where}: pending 不该带 source/date")
        else:
            if not (v.get("source") or "").startswith("https://"):
                problems.append(f"{where}: 已核对的条目必须有 https 来源")
            if not DATE.match(v.get("date") or ""):
                problems.append(f"{where}: 已核对的条目必须有 YYYY-MM-DD 核对日期")
    if problems:
        for p in problems:
            print(f"  {p}")
        raise SystemExit(f"赛事数据有 {len(problems)} 处问题")
    pending = sum(1 for c in data["competitions"] if c["verify"]["level"] == "pending")
    print(f"{len(seen)} 项赛事通过，其中 {pending} 项资格待核对", flush=True)


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    npm = tool("npm")
    if (PROJECT_ROOT / "package-lock.json").is_file():
        run([npm, "ci"], "安装前端依赖（按 lock）")
    else:
        run([npm, "install"], "安装前端依赖")


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证赛历应用")
    parser.add_argument("--skip-rust", action="store_true", help="跳过 Rust 侧检查")
    arguments = parser.parse_args()

    check_data()
    ensure_dependencies()
    run([tool("npm"), "run", "build"], "前端类型检查与构建")
    if not arguments.skip_rust:
        run(
            [tool("cargo"), "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            "Rust 侧检查",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
