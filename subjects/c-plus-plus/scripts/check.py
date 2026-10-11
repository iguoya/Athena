#!/usr/bin/env python3
"""C++ 教程的验证入口。

核对课表，然后构建前端并 cargo check。gtkmm 工程在 practice/cpp，不在这条入口
（仓库 ADR 0141）。

用法：
    python3 scripts/check.py [--skip-rust] [--content-only]
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
EXPECTED_ID = "c-plus-plus"
EXPECTED_PORT = 1512


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请先安装后重试")
    return found


def check_app_json() -> None:
    print("== app.json 一致性 ==", flush=True)
    data = json.loads((PROJECT_ROOT / "app.json").read_text(encoding="utf-8"))
    if data.get("id") != EXPECTED_ID or data.get("id") != PROJECT_ROOT.name:
        raise SystemExit(f"app.json 的 id 必须是 {EXPECTED_ID}")
    if data.get("parent") is not None:
        raise SystemExit("app.json 不应声明 parent")
    ready = data.get("dev", {}).get("ready", {})
    http = ready.get("http", "") if isinstance(ready, dict) else ""
    if not http.endswith(f":{EXPECTED_PORT}"):
        raise SystemExit(f"dev.ready.http 的端口必须是 {EXPECTED_PORT}")
    run = data.get("dev", {}).get("run", [])
    if "meson" in run or any("meson" in str(step) for step in data.get("dev", {}).get("prepare", [])):
        raise SystemExit("dev 块不应再走 Meson（ADR 0060）")


def check_ports() -> None:
    print("== 端口三方对齐 ==", flush=True)
    vite = (PROJECT_ROOT / "vite.config.ts").read_text(encoding="utf-8")
    match = re.search(r"port:\s*(\d+)", vite)
    if not match or int(match.group(1)) != EXPECTED_PORT:
        raise SystemExit(f"vite.config.ts 的 port 必须是 {EXPECTED_PORT}")
    tauri = json.loads(
        (PROJECT_ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )
    dev_url = tauri.get("build", {}).get("devUrl", "")
    if not dev_url.endswith(f"localhost:{EXPECTED_PORT}"):
        raise SystemExit(f"tauri.conf.json 的 devUrl 必须指向 localhost:{EXPECTED_PORT}")


def check_content() -> None:
    print("== 课表对齐 ==", flush=True)
    course = json.loads(
        (PROJECT_ROOT / "content" / "curriculum.json").read_text(encoding="utf-8")
    )
    seen: set[str] = set()
    for chapter in course["chapters"]:
        if not str(chapter.get("id", "")).startswith("cpp."):
            raise SystemExit(f"章 id {chapter.get('id')!r} 必须以 cpp. 开头")
        for topic in chapter["topics"]:
            tid = topic["id"]
            if tid in seen:
                raise SystemExit(f"知识点 id 重复: {tid}")
            seen.add(tid)
            if not tid.startswith(chapter["id"] + "."):
                raise SystemExit(f"{tid} 不在章 {chapter['id']} 下")
            for item in topic.get("quiz", []):
                choices = item.get("choices", [])
                if len(choices) != 4:
                    raise SystemExit(f"{tid} 的随堂题必须是 4 个选项")
                answer = item.get("answer")
                if not isinstance(answer, int) or not 0 <= answer < 4:
                    raise SystemExit(f"{tid} 的答案下标不合法")
                if not item.get("explanation"):
                    raise SystemExit(f"{tid} 的随堂题缺解析")
            for lab in topic.get("labs", []):
                case = lab.get("case", "")
                path = PROJECT_ROOT / "resources" / "cases" / case / "main.cpp"
                if not path.is_file():
                    raise SystemExit(f"{tid} 的案例不存在: {case}")
    print(f"知识点 {len(seen)} 个", flush=True)


def pnpm_build() -> None:
    print("== 前端构建 ==", flush=True)
    pnpm = tool("pnpm")
    if not (PROJECT_ROOT / "node_modules").exists():
        subprocess.run([pnpm, "install", "--frozen-lockfile"], cwd=PROJECT_ROOT, check=True)
    subprocess.run([pnpm, "run", "build"], cwd=PROJECT_ROOT, check=True)


def cargo_check() -> None:
    print("== cargo check ==", flush=True)
    cargo = tool("cargo")
    subprocess.run(
        [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml", "--tests"],
        cwd=PROJECT_ROOT,
        check=True,
    )


def main() -> None:
    _force_utf8_output()
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-rust", action="store_true")
    parser.add_argument("--content-only", action="store_true")
    args = parser.parse_args()
    check_app_json()
    check_ports()
    check_content()
    if args.content_only:
        return
    pnpm_build()
    if not args.skip_rust:
        cargo_check()


if __name__ == "__main__":
    main()
