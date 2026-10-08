#!/usr/bin/env python3
"""拾阶英语学习应用的验证入口：内容出处、lint、类型与构建、前端测试、Rust 侧。

用 Python 而不是 shell：验证是每天都要跑的环节，不该要求 Windows 上先装
Git Bash 或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py [--skip-rust]
"""

from __future__ import annotations

import argparse
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


def tool(name: str, hint: str = "") -> str:
    """把命令名解析成真实路径再执行。

    Windows 上 pnpm 实际是 pnpm.cmd，裸名交给 subprocess 会找不到；which 会按
    PATHEXT 查找，三个平台都能拿到能直接执行的路径（ADR 0047）。
    """
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请先安装后重试。{hint}")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    # shell=False：参数按列表传，路径里有空格也不会被拆开，Windows 上尤其重要。
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证拾阶英语学习应用")
    parser.add_argument(
        "--skip-rust",
        action="store_true",
        help="跳过 Rust 侧检查（只改了内容或前端时用它，能省几分钟）",
    )
    arguments = parser.parse_args()

    # Lumi 用 pnpm（pnpm-lock.yaml 里的版本约束依赖 pnpm 的 minimumReleaseAge，换成 npm
    # 会装出另一套依赖）。corepack enable 即可启用，不必单独安装。
    pnpm = tool("pnpm", "先运行 `corepack enable`（Node 22+ 自带 corepack）。")
    if not (PROJECT_ROOT / "node_modules").is_dir():
        run([pnpm, "install", "--frozen-lockfile"], "安装前端依赖（按 lock）")

    # 先查内容：每条词和句子都要有登记在 content/sources.json 的出处（本应用 ADR 0019）。
    run([pnpm, "content:check"], "内容出处检查")
    run([pnpm, "lint"], "ESLint")
    run([pnpm, "build"], "前端类型检查与构建")
    run([pnpm, "test"], "前端测试")

    if not arguments.skip_rust:
        # 不设 CARGO_TARGET_DIR：尊重外部环境；单独跑时用应用自己的 src-tauri/target。
        cargo = tool("cargo")
        run(
            [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            "Rust 侧检查",
        )
        run([cargo, "test", "--manifest-path", "src-tauri/Cargo.toml"], "Rust 侧测试")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
