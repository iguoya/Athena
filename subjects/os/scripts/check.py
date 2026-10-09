#!/usr/bin/env python3
"""操作系统应用的验证入口。

骨架阶段（ADR 0103）默认只做结构校验：app.json 一致性（id/parent/端口三方
对齐）、内容 JSON 语法、课程节前缀、出处契约、图标齐备；--full 追加前端
构建与 Rust 检查。内容开始填充后把 DEFAULT_FULL 翻转为 True。

用 Python 而不是 shell：验证是每天都要跑的环节，不该要求 Windows 上先装
Git Bash 或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py [--full] [--skip-rust]
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

EXPECTED_ID = "os"
EXPECTED_PARENT = "software"
EXPECTED_PORT = 1492
DEFAULT_FULL = False


def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8，打印中文会抛 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    """把命令名解析成真实路径再执行（Windows 上 npm 实际是 npm.cmd）。"""
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请先安装后重试")
    return found


def check_app_json() -> None:
    print("== app.json 一致性 ==", flush=True)
    path = PROJECT_ROOT / "app.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("id") != EXPECTED_ID or data.get("id") != PROJECT_ROOT.name:
        raise SystemExit(f"app.json 的 id 必须是 {EXPECTED_ID}（与目录名一致）")
    if data.get("parent") != EXPECTED_PARENT:
        raise SystemExit(f"app.json 的 parent 必须是 {EXPECTED_PARENT}（ADR 0103）")
    port = re.search(r":(\d+)$", data.get("dev", {}).get("ready", {}).get("http", ""))
    if not port or int(port.group(1)) != EXPECTED_PORT:
        raise SystemExit(f"dev.ready.http 的端口必须是 {EXPECTED_PORT}")
    renders = data.get("icon", {}).get("renders", {})
    missing = [rel for rel in renders if not (PROJECT_ROOT / rel).exists()]
    if missing:
        raise SystemExit("图标文件缺失: " + ", ".join(missing))


def check_ports() -> None:
    """端口在 app.json / vite.config.ts / tauri.conf.json 三处声明，最容易漂移。"""
    print("== 端口三方对齐 ==", flush=True)
    vite = (PROJECT_ROOT / "vite.config.ts").read_text(encoding="utf-8")
    m = re.search(r"port:\s*(\d+)", vite)
    if not m or int(m.group(1)) != EXPECTED_PORT:
        raise SystemExit(f"vite.config.ts 的 port 必须是 {EXPECTED_PORT}")
    tauri = json.loads(
        (PROJECT_ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )
    dev_url = tauri.get("build", {}).get("devUrl", "")
    if not dev_url.endswith(f"localhost:{EXPECTED_PORT}"):
        raise SystemExit(f"tauri.conf.json 的 devUrl 必须指向 localhost:{EXPECTED_PORT}")


def check_content() -> None:
    print("== 内容 JSON 校验 ==", flush=True)
    files = sorted((PROJECT_ROOT / "content").rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有任何 JSON，内容目录是不是错了？")
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}")
    course = json.loads(
        (PROJECT_ROOT / "content" / "course.json").read_text(encoding="utf-8")
    )
    sections = course.get("sections")
    if not isinstance(sections, list) or not sections:
        raise SystemExit("course.json 缺 sections 列表")
    for section in sections:
        sid = section.get("id", "")
        if not sid.startswith("os."):
            raise SystemExit(f"节 id {sid!r} 必须用 os. 前缀（知识点前缀与"
                             "目录 id 解耦，ADR 0097 决策 3 同规）")
        if not section.get("title"):
            raise SystemExit(f"节 {sid} 缺 title")


def check_contract() -> None:
    print("== 出处契约 ==", flush=True)
    contract = json.loads(
        (PROJECT_ROOT / "content-contract.json").read_text(encoding="utf-8")
    )
    if contract.get("tier") != "exam":
        raise SystemExit("content-contract.json 的 tier 必须是 exam（ADR 0089、0103）")
    if contract.get("catalog") != "sources.json":
        raise SystemExit("catalog 必须指向 content/sources.json")
    sources = json.loads(
        (PROJECT_ROOT / "content" / "sources.json").read_text(encoding="utf-8")
    )
    if not sources.get("sources"):
        raise SystemExit("sources.json 的 sources 列表为空")


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def check_build(skip_rust: bool) -> None:
    node_modules = PROJECT_ROOT / "node_modules"
    if not node_modules.exists():
        run([tool("npm"), "install"], "安装前端依赖")
    run([tool("npm"), "run", "build"], "前端构建")
    if not skip_rust:
        cargo = tool("cargo")
        run([cargo, "check"], "Rust cargo check")


def main() -> None:
    _force_utf8_output()
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="追加构建检查")
    parser.add_argument("--skip-rust", action="store_true", help="--full 时跳过 cargo")
    args = parser.parse_args()

    check_app_json()
    check_ports()
    check_content()
    check_contract()
    if args.full or DEFAULT_FULL:
        check_build(args.skip_rust)
    print("OK", flush=True)


if __name__ == "__main__":
    main()
