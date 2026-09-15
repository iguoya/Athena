#!/usr/bin/env python3
"""Atlas 的独立验证入口：先验证内容 JSON，再构建并运行领域测试。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请安装后重试")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def check_json() -> None:
    print("== 内容 JSON 解析 ==", flush=True)
    files = sorted((PROJECT_ROOT / "content").rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有 JSON 文件")
    for path in files + [PROJECT_ROOT / "content-contract.json", PROJECT_ROOT / "app.json"]:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error
    print(f"{len(files)} 个内容 JSON 解析通过", flush=True)


def main() -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="验证 Atlas：内容、构建和路线图领域测试")
    parser.add_argument("--build-dir", default="build", help="构建目录（默认 build）")
    parser.add_argument("--buildtype", default="Debug", help="CMake 构建类型（默认 Debug）")
    arguments = parser.parse_args()

    check_json()
    cmake = tool("cmake")
    configure = [cmake, "-S", ".", "-B", arguments.build_dir, f"-DCMAKE_BUILD_TYPE={arguments.buildtype}"]
    if shutil.which("ninja") is not None:
        configure += ["-G", "Ninja"]
    run(configure, "CMake 配置")
    run([cmake, "--build", arguments.build_dir, "--config", arguments.buildtype], "构建")
    run(["ctest", "--test-dir", arguments.build_dir, "--output-on-failure", "-C", arguments.buildtype], "领域测试")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
