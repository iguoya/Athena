#!/usr/bin/env python3
"""数学学习应用的验证入口：内容校验、前端构建、Rust 侧类型检查。

用 Python 而不是 shell：验证是每天都要跑的环节，不该要求 Windows 上先装
Git Bash 或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py [--skip-rust]
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
    """把命令名解析成真实路径再执行。

    Windows 上 npm 实际是 npm.cmd，直接把裸名交给 subprocess 会找不到；
    which 会按 PATHEXT 查找，三个平台都能拿到能直接执行的路径（ADR 0047）。
    """
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
    """内容全是 JSON，坏一个文件前端就白屏。先校验再谈构建。"""
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


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    # 有 lock 就按 lock 装：CI 上每次拿到的依赖要和本地一致。
    npm = tool("npm")
    if (PROJECT_ROOT / "package-lock.json").is_file():
        run([npm, "ci"], "安装前端依赖（按 lock）")
    else:
        run([npm, "install"], "安装前端依赖")


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证数学学习应用")
    parser.add_argument(
        "--skip-rust",
        action="store_true",
        help="跳过 Rust 侧检查（只改了内容或前端时用它，能省几分钟）",
    )
    arguments = parser.parse_args()

    check_json()
    ensure_dependencies()
    # npm run build = lint-content + test-speech + tsc + vite build：内容 lint、
    # 朗读用例、类型和打包一次过。这些检查留在 npm 那边，本地 npm run build
    # 也会跑到它们。
    run([tool("npm"), "run", "build"], "前端类型检查与构建")

    if not arguments.skip_rust:
        # 不设 CARGO_TARGET_DIR：尊重外部环境。编排器会注入共享目录，
        # 单独跑时就用应用自己的 src-tauri/target。
        # 引擎测试要用 engine/.venv 里的 Python。先建好——它是本应用最核心的
        # 那条链路（Rust↔Python↔SymPy），不该因为环境没准备就被跳过。
        run([sys.executable, "scripts/setup-engine.py"], "准备符号引擎环境")
        cargo = tool("cargo")
        run(
            [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            "Rust 侧检查",
        )
        # 跑测试，不只是编译。apps/cpp 在 Windows 上那个 CRLF 问题就是测试逮到的
        # ——只 check 的话它会一路绿到运行时才炸。
        run(
            [cargo, "test", "--manifest-path", "src-tauri/Cargo.toml"],
            "Rust 侧测试",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
