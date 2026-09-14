#!/usr/bin/env python3
"""C++ 教程的验证入口：JSON 校验、生成器检查、构建与测试。

用 Python 而不是 shell：验证是每天都要跑的环节，不该要求 Windows 上先装
Git Bash 或 WSL（ADR 0047）。Python 三个平台都自带，仓库里生成器和打包器
本来就是 Python。

用法：
    python3 scripts/check.py [--build-dir DIR] [--buildtype TYPE]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    # shell=False：参数按列表传，路径里有空格也不会被拆开，Windows 上尤其重要。
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def meson() -> str:
    found = shutil.which("meson")
    if found is None:
        raise SystemExit("找不到 meson，请先安装（pip install meson 或包管理器）")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 C++ 教程：校验、构建、测试")
    parser.add_argument("--build-dir", default="build", help="构建目录（默认 build）")
    parser.add_argument("--buildtype", help="传给 meson setup 的 --buildtype")
    arguments = parser.parse_args()

    print("== JSON 校验 ==", flush=True)
    config = PROJECT_ROOT / "resources" / "athena.json"
    json.loads(config.read_text(encoding="utf-8"))

    run(
        [
            sys.executable,
            "scripts/generate_project.py",
            "--project-root",
            ".",
            "--config",
            "resources/athena.json",
            "check",
        ],
        "生成器检查",
    )

    build_dir = arguments.build_dir
    setup = [meson(), "setup", build_dir]
    if (PROJECT_ROOT / build_dir).is_dir():
        setup.append("--reconfigure")
    if arguments.buildtype:
        setup.append(f"--buildtype={arguments.buildtype}")
    run(setup, "Meson 配置")

    run([meson(), "compile", "-C", build_dir], "构建")
    run([meson(), "test", "-C", build_dir, "--print-errorlogs"], "测试")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
