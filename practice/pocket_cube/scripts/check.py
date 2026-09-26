#!/usr/bin/env python3
"""PocketCube 的验证入口：构建与测试。

测试源码在 practice/tests/，由本目录的 meson.build 引用（头文件带 pocket_cube/
前缀，见 meson.build 里 practice_root 的注释），所以这里只需要跑 Meson。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash
或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py [--build-dir DIR] [--buildtype TYPE]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8，打印中文会抛 UnicodeEncodeError（ADR 0047）。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def meson() -> str:
    found = shutil.which("meson")
    if found is None:
        raise SystemExit("找不到 meson，请先安装（pip install meson 或包管理器）")
    return found


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证 PocketCube：构建、测试")
    parser.add_argument("--build-dir", default="build", help="构建目录（默认 build）")
    parser.add_argument("--buildtype", help="传给 meson setup 的 --buildtype")
    arguments = parser.parse_args()

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
