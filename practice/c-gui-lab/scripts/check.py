#!/usr/bin/env python3
"""C GUI Lab 的验证入口：结构完整性 + Electron 语法 + 原生程序增量编译。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash
或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py [--skip-build]
"""

from __future__ import annotations

import argparse
import py_compile
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


def step(title: str) -> None:
    print(f"== {title} ==", flush=True)


def fail(message: str) -> None:
    print(f"  ✗ {message}")
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"  ✓ {message}")


REQUIRED_FILES = [
    "app.json",
    "CMakeLists.txt",
    "CMakePresets.json",
    "launcher/main.js",
    "launcher/preload.js",
    "launcher/index.html",
    "apps/gtk-style/gtk-style.c",
    "apps/gtk-style/style.css",
    "apps/imgui-style/imgui_style.cpp",
    "apps/lvgl-style/lvgl_style.c",
    "apps/lvgl-style/lv_conf.h",
    "apps/lvgl-style/cjk_font.c",
    "apps/lvgl-style/font_cn_20.c",
    "apps/lvgl-style/font_cn_28.c",
    "apps/raygui-demo/CMakeLists.txt",
    "apps/nuklear-demo/CMakeLists.txt",
]


def check_structure() -> None:
    step("结构完整性")
    missing = [rel for rel in REQUIRED_FILES if not (PROJECT_ROOT / rel).is_file()]
    for rel in REQUIRED_FILES:
        if rel not in missing:
            ok(rel)
    if missing:
        fail("缺少文件：" + "、".join(missing))


def check_electron_syntax() -> None:
    step("Electron 主进程语法")
    for js in ("launcher/main.js", "launcher/preload.js"):
        py_compile.compile  # noqa: B018  占位避免 linter 误报未使用
        completed = subprocess.run(
            ["node", "--check", str(PROJECT_ROOT / js)],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            fail(f"{js} 语法错误：{completed.stderr.strip()}")
        ok(js)


def check_build() -> None:
    step("原生程序增量编译")
    if not (PROJECT_ROOT / "build").is_dir():
        print("  – build/ 不存在，跳过（先跑 cmake --preset ucrt64）")
        return
    completed = subprocess.run(
        ["cmake", "--build", "--preset", "ucrt64"],
        cwd=PROJECT_ROOT,
    )
    if completed.returncode != 0:
        fail("编译失败")
    for exe in (
        "build/apps/gtk-style/gtk-style.exe",
        "build/apps/imgui-style/imgui-style.exe",
        "build/apps/lvgl-style/lvgl-style.exe",
        "build/apps/raygui-demo/raygui-demo.exe",
        "build/apps/nuklear-demo/nuklear-demo.exe",
        "build/apps/nuklear-gdi-demo/nuklear-gdi-demo.exe",
        "build/apps/microui-demo/microui-demo.exe",
    ):
        if not (PROJECT_ROOT / exe).is_file():
            fail(f"产物缺失：{exe}")
        ok(exe)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-build", action="store_true", help="跳过编译")
    args = parser.parse_args()

    _force_utf8_output()
    check_structure()
    check_electron_syntax()
    if not args.skip_build:
        check_build()
    print("全部通过")


if __name__ == "__main__":
    main()
