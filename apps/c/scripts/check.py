#!/usr/bin/env python3
"""C 语言教程的验证入口：内容校验、CMake 配置与构建。

用 Python 而不是 shell：验证是每天都要跑的环节，不该要求 Windows 上先装
Git Bash 或 WSL（ADR 0047）。

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


def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8，打印中文会抛 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    """把命令名解析成真实路径再执行；which 在三个平台上都按本地规则查找。"""
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请先安装后重试")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    # shell=False：参数按列表传，路径里有空格也不会被拆开，Windows 上尤其重要。
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def check_json() -> None:
    """课表和习题都是 JSON，坏一个文件应用就起不来。先校验再谈构建。"""
    print("== 内容 JSON 校验 ==", flush=True)
    files = sorted((PROJECT_ROOT / "content").rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有任何 JSON，内容目录是不是错了？")
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error
    print(f"{len(files)} 个 JSON 文件解析通过", flush=True)


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证 C 语言教程：校验、配置、构建")
    parser.add_argument("--build-dir", default="build", help="构建目录（默认 build）")
    parser.add_argument(
        "--buildtype",
        default="Debug",
        help="传给 CMake 的 CMAKE_BUILD_TYPE（默认 Debug）",
    )
    arguments = parser.parse_args()

    check_json()

    cmake = tool("cmake")
    configure = [
        cmake,
        "-S",
        ".",
        "-B",
        arguments.build_dir,
        f"-DCMAKE_BUILD_TYPE={arguments.buildtype}",
    ]
    # 有 Ninja 就用 Ninja：Windows 上 CMake 默认挑 Visual Studio，那是多配置
    # 生成器，产物会落在 build/Debug/ 而不是 build/，和 app.json 的
    # `dev.run: build/athena-c` 对不上。指定单配置生成器，三个平台的布局就一致了。
    if shutil.which("ninja") is not None:
        configure += ["-G", "Ninja"]
    run(configure, "CMake 配置")
    # --config 只有多配置生成器（Visual Studio、Xcode）认，单配置生成器忽略它，
    # 所以三个平台可以共用这一条命令。
    run(
        [cmake, "--build", arguments.build_dir, "--config", arguments.buildtype],
        "构建",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
