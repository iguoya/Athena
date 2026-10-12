#!/usr/bin/env python3
"""中国象棋应用的验证入口。

默认只做结构校验：app.json、端口、课表、出处契约、五章十个窗口的文件齐备。
CI 没有 gtkmm，不能把 meson 编进默认检查。本机要连棋盘一起编，加 --native。
--full 追加教程壳的前端构建和 cargo check，仍然不编 gtkmm。

用法：
    python3 scripts/check.py
    python3 scripts/check.py --full
    python3 scripts/check.py --native
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_ID = "chinese-chess"
EXPECTED_PORT = 1513
DEFAULT_FULL = False
CHAPTERS = ("01-window", "02-layout", "03-board", "04-pieces", "05-move")


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str, env: dict[str, str] | None = None) -> str:
    found = shutil.which(name, path=None if env is None else env.get("PATH"))
    if found is None:
        raise SystemExit(f"找不到 {name}，请先安装后重试")
    return found


def toolchain_env() -> dict[str, str]:
    env = os.environ.copy()
    mingw = Path(r"C:\msys64\mingw64")
    if mingw.joinpath("bin").is_dir():
        env["PATH"] = str(mingw / "bin") + os.pathsep + env.get("PATH", "")
        env["PKG_CONFIG_PATH"] = str(mingw / "lib" / "pkgconfig")
    return env


def check_app_json() -> None:
    print("== app.json 一致性 ==", flush=True)
    data = json.loads((PROJECT_ROOT / "app.json").read_text(encoding="utf-8"))
    if data.get("id") != EXPECTED_ID or data.get("id") != PROJECT_ROOT.name:
        raise SystemExit(f"app.json 的 id 必须是 {EXPECTED_ID}（与目录名一致）")
    if data.get("group") != "程序设计":
        raise SystemExit('app.json 的 group 必须是 "程序设计"')
    if data.get("parent"):
        raise SystemExit("本应用不挂靠，app.json 不能有 parent")
    port = re.search(r":(\d+)$", data.get("dev", {}).get("ready", {}).get("http", ""))
    if not port or int(port.group(1)) != EXPECTED_PORT:
        raise SystemExit(f"dev.ready.http 的端口必须是 {EXPECTED_PORT}")
    renders = data.get("icon", {}).get("renders", {})
    missing = [rel for rel in renders if not (PROJECT_ROOT / rel).exists()]
    if missing:
        raise SystemExit("图标文件缺失: " + ", ".join(missing))


def check_ports() -> None:
    print("== 端口三方对齐 ==", flush=True)
    vite = (PROJECT_ROOT / "vite.config.ts").read_text(encoding="utf-8")
    match = re.search(r"port:\s*(\d+)", vite)
    if not match or int(match.group(1)) != EXPECTED_PORT:
        raise SystemExit(f"vite.config.ts 的 port 必须是 {EXPECTED_PORT}")
    tauri = json.loads((PROJECT_ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    dev_url = tauri.get("build", {}).get("devUrl", "")
    if not dev_url.endswith(f"localhost:{EXPECTED_PORT}"):
        raise SystemExit(f"tauri.conf.json 的 devUrl 必须指向 localhost:{EXPECTED_PORT}")


def check_content() -> None:
    print("== 内容 JSON 校验 ==", flush=True)
    files = sorted((PROJECT_ROOT / "content").rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有任何 JSON")
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error
    course = json.loads((PROJECT_ROOT / "content" / "course.json").read_text(encoding="utf-8"))
    sections = course.get("sections")
    if not isinstance(sections, list) or len(sections) != len(CHAPTERS):
        raise SystemExit(f"course.json 必须有 {len(CHAPTERS)} 节")
    for section, chapter in zip(sections, CHAPTERS, strict=True):
        sid = section.get("id", "")
        if not sid.startswith("chess."):
            raise SystemExit(f"节 id {sid!r} 必须用 chess. 前缀")
        if section.get("exercise") != chapter:
            raise SystemExit(f"节 {sid} 的 exercise 必须是 {chapter}")
        path = PROJECT_ROOT / "content" / "chapters" / f"{chapter}.json"
        lesson = json.loads(path.read_text(encoding="utf-8"))
        if lesson.get("id") != sid:
            raise SystemExit(f"{path.name} 的 id 与课表不一致")
        sections = lesson.get("sections") or []
        if not any(item.get("role") == "focus" for item in sections):
            raise SystemExit(f"{path.name} 缺少界面文件的重点讲解")
        if not any(item.get("role") == "compare" for item in sections):
            raise SystemExit(f"{path.name} 缺少代码版对照")
        cooperation = lesson.get("cooperation")
        if not isinstance(cooperation, dict) or not cooperation.get("intro"):
            raise SystemExit(f"{path.name} 缺少函数配合说明")
        roster = cooperation.get("roster")
        figures = cooperation.get("figures")
        if not isinstance(roster, list) or not roster:
            raise SystemExit(f"{path.name} 缺少函数分工")
        if not isinstance(figures, list) or not figures:
            raise SystemExit(f"{path.name} 缺少配合图")
        for item in roster:
            if not item.get("name") or not item.get("role") or not item.get("with"):
                raise SystemExit(f"{path.name} 的职责表缺名字、职责或协作者")
        for figure in figures:
            if figure.get("kind") not in ("flow", "sequence", "dependency") or not figure.get("title"):
                raise SystemExit(f"{path.name} 的图种类或标题不对")
            if figure.get("kind") == "dependency":
                for link in figure.get("links") or []:
                    if link.get("style") not in ("call", "signal"):
                        raise SystemExit(f"{path.name} 的依赖箭头必须是调用或信号")
        questions = lesson.get("questions") or []
        if not questions:
            raise SystemExit(f"{path.name} 没有题目")
        seen: set[str] = set()
        for question in questions:
            qid = question.get("id", "")
            if not qid.startswith("chess.") or qid in seen:
                raise SystemExit(f"{path.name} 的题目 id 不合法：{qid!r}")
            seen.add(qid)
            if not question.get("stem") or not question.get("choices"):
                raise SystemExit(f"{qid} 缺题干或选项")
            if not question.get("source_refs"):
                raise SystemExit(f"{qid} 缺 source_refs")
        runs = lesson.get("runs") or []
        if len(runs) != 2 or not runs[0].get("id", "").endswith("/ui") or not runs[1].get("id", "").endswith("/code"):
            raise SystemExit(f"{path.name} 要先给出界面文件版、再给出代码版两个运行 id")
        rust = (PROJECT_ROOT / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
        for run in runs:
            if f'"{run["id"]}"' not in rust:
                raise SystemExit(f"{run['id']} 不在教程壳的白名单里")
        files = lesson.get("files") or []
        if not files or not files[0].endswith("window.blp"):
            raise SystemExit(f"{path.name} 的文件列表要以 window.blp 开头")


def check_exercises() -> None:
    print("== 章节子程序 ==", flush=True)
    for chapter in CHAPTERS:
        root = PROJECT_ROOT / "exercise" / chapter
        required = [
            root / "meson.build",
            root / "code" / "main.cc",
            root / "ui" / "main.cc",
            root / "ui" / "window.blp",
            root / "ui" / "style.css",
            root / "ui" / "app.gresource.xml",
        ]
        missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
        if missing:
            raise SystemExit(f"{chapter} 缺 " + ", ".join(missing))
        for main in (root / "code" / "main.cc", root / "ui" / "main.cc"):
            if "NON_UNIQUE" not in main.read_text(encoding="utf-8"):
                raise SystemExit(f"{main.relative_to(PROJECT_ROOT)} 要标 NON_UNIQUE，两套窗口才能同时开")


def check_contract() -> None:
    print("== 出处契约 ==", flush=True)
    contract = json.loads((PROJECT_ROOT / "content-contract.json").read_text(encoding="utf-8"))
    if contract.get("tier") != "open":
        raise SystemExit("content-contract.json 的 tier 必须是 open")
    if contract.get("catalog") != "sources.json":
        raise SystemExit("catalog 必须指向 content/sources.json")
    sources = json.loads((PROJECT_ROOT / "content" / "sources.json").read_text(encoding="utf-8"))
    if not sources.get("sources"):
        raise SystemExit("sources.json 的 sources 列表为空")


def run(command: list[str], step: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=cwd or PROJECT_ROOT, env=env)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def check_build(skip_rust: bool) -> None:
    if not (PROJECT_ROOT / "node_modules").exists():
        run([tool("pnpm"), "install", "--frozen-lockfile"], "安装前端依赖（按仓库根 lock）")
    run([tool("pnpm"), "run", "build"], "前端构建")
    if not skip_rust:
        manifest = PROJECT_ROOT / "src-tauri" / "Cargo.toml"
        run([tool("cargo"), "check", "--manifest-path", str(manifest)], "Rust cargo check")


def check_native() -> None:
    print("== 编译十个 gtkmm 窗口 ==", flush=True)
    env = toolchain_env()
    meson = tool("meson", env)
    for chapter in CHAPTERS:
        root = PROJECT_ROOT / "exercise" / chapter
        if not (root / "build" / "build.ninja").is_file():
            run([meson, "setup", "build"], f"{chapter} 配置", env=env, cwd=root)
        run([meson, "compile", "-C", "build"], f"{chapter} 编译", env=env, cwd=root)
    rules = PROJECT_ROOT / "exercise" / "05-move"
    run([meson, "test", "-C", "build"], "走子规则测试", env=env, cwd=rules)


def main() -> None:
    _force_utf8_output()
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="追加教程壳的前端构建与 cargo check")
    parser.add_argument("--skip-rust", action="store_true", help="--full 时跳过 cargo")
    parser.add_argument("--native", action="store_true", help="用 meson 编译 exercise/ 下的十个 gtkmm 窗口")
    args = parser.parse_args()

    check_app_json()
    check_ports()
    check_content()
    check_exercises()
    check_contract()
    if args.native:
        check_native()
    if args.full or DEFAULT_FULL:
        check_build(args.skip_rust)
    print("OK", flush=True)


if __name__ == "__main__":
    main()
