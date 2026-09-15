#!/usr/bin/env python3
"""按当前平台调用 flutter。找不到 PATH 里的 SDK 时，再试 ~/flutter。

无参数：flutter run -d macos|windows|linux
有参数：原样转给 flutter，例如 pub get。
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent


def flutter_bin() -> str:
    found = shutil.which("flutter")
    if found:
        return found
    name = "flutter.bat" if os.name == "nt" else "flutter"
    candidate = Path.home() / "flutter" / "bin" / name
    if candidate.is_file():
        return str(candidate)
    raise SystemExit("找不到 flutter。把 SDK 放进 PATH，或安装到 ~/flutter。")


def desktop_device() -> str:
    mapping = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}
    system = platform.system()
    if system not in mapping:
        raise SystemExit(f"没有为 {system} 配置桌面设备")
    return mapping[system]


def main(argv: list[str]) -> int:
    flutter = flutter_bin()
    command = [flutter, *argv] if argv else [flutter, "run", "-d", desktop_device()]
    env = os.environ.copy()
    env.setdefault("ATHENA_DRIVING_ROOT", str(APP_ROOT))
    return subprocess.call(command, cwd=APP_ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
