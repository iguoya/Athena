#!/usr/bin/env python3
"""协作观察台的验证入口:关键配置一致性 + 前端构建 + Rust 侧检查。

没有内容目录(观察台不存内容),所以比课程应用少一块内容校验;
三处端口(app.json / vite.config.ts / tauri.conf.json)一致是启动器
拉得起来的前提,这里硬校验。

用法:
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
EXPECTED_ID = "comms-console"
EXPECTED_PORT = 1521


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    """Windows 上 pnpm 实际是 pnpm.cmd,which 按 PATHEXT 查出可执行路径(ADR 0047)。"""
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name},请先安装后重试。")
    return found


def fail(msg: str) -> None:
    raise SystemExit(f"校验失败:{msg}")


def check_config() -> None:
    app = json.loads((PROJECT_ROOT / "app.json").read_text(encoding="utf-8"))
    if app.get("id") != EXPECTED_ID:
        fail(f"app.json 的 id 应为 {EXPECTED_ID},实际 {app.get('id')!r}")
    port = app.get("dev", {}).get("ready", {}).get("http", "")
    if not port.endswith(f":{EXPECTED_PORT}"):
        fail(f"app.json 的 dev.ready.http 端口应为 {EXPECTED_PORT},实际 {port!r}")
    if app.get("dev", {}).get("binary") != "athena-comms-console":
        fail("app.json 的 dev.binary 应为 athena-comms-console")

    vite = (PROJECT_ROOT / "vite.config.ts").read_text(encoding="utf-8")
    if f"port: {EXPECTED_PORT}" not in vite:
        fail(f"vite.config.ts 的端口应为 {EXPECTED_PORT}")

    tauri = json.loads((PROJECT_ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    if tauri.get("build", {}).get("devUrl") != f"http://localhost:{EXPECTED_PORT}":
        fail(f"tauri.conf.json 的 devUrl 端口应为 {EXPECTED_PORT}")
    if not tauri.get("productName", "").startswith("athena-comms-console"):
        fail("tauri.conf.json 的 productName 应为 athena-comms-console")

    for view in ("BoardView", "TaskView", "ChatView", "StatsView"):
        if not (PROJECT_ROOT / "src" / "views" / f"{view}.tsx").is_file():
            fail(f"缺视图组件 src/views/{view}.tsx")

    if not (PROJECT_ROOT / "icon.svg").is_file():
        fail("缺 icon.svg(ADR 0065)")
    print("配置一致:id/port/binary/视图组件/图标", flush=True)


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    repo_lock = PROJECT_ROOT.parents[1] / "pnpm-lock.yaml"
    if repo_lock.is_file():
        subprocess.run([tool("pnpm"), "install", "--frozen-lockfile"], cwd=PROJECT_ROOT, check=True)
    else:
        subprocess.run([tool("pnpm"), "install"], cwd=PROJECT_ROOT, check=True)


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证协作观察台")
    parser.add_argument("--skip-rust", action="store_true", help="跳过 Rust 侧检查")
    args = parser.parse_args()

    check_config()
    ensure_dependencies()
    # pnpm run build = tsc + vite build,类型和打包一次过。
    subprocess.run([tool("pnpm"), "run", "build"], cwd=PROJECT_ROOT, check=True)

    if not args.skip_rust:
        cargo = tool("cargo")
        subprocess.run(
            [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            cwd=PROJECT_ROOT, check=True,
        )
        subprocess.run([cargo, "test", "--manifest-path", "src-tauri/Cargo.toml"], cwd=PROJECT_ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
