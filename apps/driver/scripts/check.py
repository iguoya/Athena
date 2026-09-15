#!/usr/bin/env python3
"""驾驶学习应用的验证入口：内容 JSON、出处合约由仓库根检查，这里跑分析与测试。

用 Python 而不是 shell（ADR 0047）。

用法：
    python3 scripts/check.py
    python3 scripts/check.py --skip-build
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def flutter_bin() -> str:
    found = shutil.which("flutter")
    if found:
        return found
    name = "flutter.bat" if os.name == "nt" else "flutter"
    candidate = Path.home() / "flutter" / "bin" / name
    if candidate.is_file():
        return str(candidate)
    raise SystemExit("找不到 flutter。把 SDK 放进 PATH，或安装到 ~/flutter。")


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def check_json() -> None:
    print("== 内容 JSON 校验 ==", flush=True)
    files = sorted((PROJECT_ROOT / "content").rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有任何 JSON")
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error
    print(f"{len(files)} 个 JSON 文件解析通过", flush=True)


def desktop_target() -> str:
    mapping = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}
    system = platform.system()
    if system not in mapping:
        raise SystemExit(f"没有为 {system} 配置桌面构建目标")
    return mapping[system]


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证驾驶学习应用")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="只跑分析与测试，不编桌面目标（改内容时够用）",
    )
    arguments = parser.parse_args()

    check_json()
    flutter = flutter_bin()
    run([flutter, "pub", "get"], "安装 Dart 依赖")
    run([flutter, "analyze"], "静态分析")
    run([flutter, "test"], "测试")
    if not arguments.skip_build:
        target = desktop_target()
        run([flutter, "build", target, "--debug"], f"构建 {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
