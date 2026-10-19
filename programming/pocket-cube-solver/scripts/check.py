#!/usr/bin/env python3
"""二阶魔方应用的验证入口。

默认只做结构校验：app.json、端口、课表、出处契约、七章窗口的文件齐备，并用 Node 核对
魔方模型（C++ 与 TypeScript 两份）的黄金向量和讲解里每张回放图。
CI 没有 gtkmm，不能把 meson 编进默认检查。本机要连魔方一起编，加 --native。
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

EXPECTED_ID = "pocket-cube-solver"
EXPECTED_PORT = 1522
DEFAULT_FULL = False
CHAPTERS = ("01-net", "02-turns", "03-layer", "04-orient", "05-permute", "06-solver", "07-optimal")
PREFIX = "cube."


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
    sources = json.loads((PROJECT_ROOT / "content" / "sources.json").read_text(encoding="utf-8"))
    source_ids = {item["id"] for item in sources.get("sources", [])}
    rust = (PROJECT_ROOT / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
    # 防猜题捷径：全课答案位置不能扎堆，正确项也不能总是最长的那个（2026-10-19 审查时
    # 29 题里 20 题答案在第 2 位、26 题正确项最长，不看题干也能蒙对）
    answer_counts: dict[int, int] = {}
    longest_hits = longest_total = 0
    for section, chapter in zip(sections, CHAPTERS, strict=True):
        sid = section.get("id", "")
        if not sid.startswith(PREFIX):
            raise SystemExit(f"节 id {sid!r} 必须用 {PREFIX} 前缀")
        if section.get("exercise") != chapter:
            raise SystemExit(f"节 {sid} 的 exercise 必须是 {chapter}")
        path = PROJECT_ROOT / "content" / "chapters" / f"{chapter}.json"
        lesson = json.loads(path.read_text(encoding="utf-8"))
        if lesson.get("id") != sid:
            raise SystemExit(f"{path.name} 的 id 与课表不一致")
        if lesson.get("exercise") != chapter:
            raise SystemExit(f"{path.name} 的 exercise 必须是 {chapter}")
        if not lesson.get("lead"):
            raise SystemExit(f"{path.name} 缺导语（写明这一章回答的那一个问题）")
        parts = lesson.get("sections") or []
        if not any(item.get("role") == "focus" for item in parts):
            raise SystemExit(f"{path.name} 缺少重点讲解")
        for item in parts:
            if item.get("role") not in ("focus", "advanced", "experiment"):
                raise SystemExit(f"{path.name} 的讲解节 role 只能是 focus、advanced 或 experiment")
            if item.get("role") == "experiment" and not all(item.get(k) for k in ("heading", "body", "predict", "observe")):
                raise SystemExit(f"{path.name} 的试一试要写全做什么（body）、先猜什么（predict）、实测结果（observe）")
            figure = item.get("figure")
            if figure is not None and figure.get("kind") not in ("cube", "bars"):
                raise SystemExit(f"{path.name} 的讲解图种类只能是 cube 或 bars")
            if figure is not None and not (figure.get("title") and figure.get("caption")):
                raise SystemExit(f"{path.name} 的讲解图缺标题或说明")
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
            for slot in ("figure", "reveal"):
                visual = question.get(slot)
                if visual is not None and (visual.get("kind") != "cube" or not (visual.get("title") and visual.get("caption"))):
                    raise SystemExit(f"{path.name} 题 {question.get('id')} 的 {slot} 只能是带标题和说明的魔方图")
                if slot == "figure" and visual is not None and visual.get("moves"):
                    raise SystemExit(f"{path.name} 题 {question.get('id')} 的题干图不能带 moves（会把答案摆在题干里），回放放进 reveal")
            qid = question.get("id", "")
            if not qid.startswith(PREFIX) or qid in seen:
                raise SystemExit(f"{path.name} 的题目 id 不合法：{qid!r}")
            seen.add(qid)
            choices = question.get("choices") or []
            if not question.get("stem") or len(choices) < 2 or len(set(choices)) != len(choices):
                raise SystemExit(f"{qid} 缺题干，或选项少于 2 个、有重复")
            if not isinstance(question.get("answer"), int) or not 0 <= question["answer"] < len(choices):
                raise SystemExit(f"{qid} 的 answer 不是有效的选项序号")
            if not question.get("explanation"):
                raise SystemExit(f"{qid} 缺解析")
            for choice in choices:
                if "（" in choice or "(" in choice:
                    raise SystemExit(f"{qid} 的选项里有括号注释：{choice!r}。常见错误写进解析，不写进选项")
            answer_counts[question["answer"]] = answer_counts.get(question["answer"], 0) + 1
            longest_total += 1
            longest_hits += all(len(choices[question["answer"]]) > len(c) for i, c in enumerate(choices) if i != question["answer"])
            refs = question.get("source_refs") or []
            if not refs:
                raise SystemExit(f"{qid} 缺 source_refs")
            for ref in refs:
                if ref.get("source_id") not in source_ids:
                    raise SystemExit(f"{qid} 引用了没有登记的来源 {ref.get('source_id')!r}")
                if ref.get("relation") == "authored" and not ref.get("note"):
                    raise SystemExit(f"{qid} 标了 authored 却没写为什么没有现成题")
        runs = lesson.get("runs") or []
        if len(runs) != 1 or runs[0].get("id") != chapter:
            raise SystemExit(f"{path.name} 要恰好一个运行入口，id 就是章节目录 {chapter}")
        if f'"{chapter}"' not in rust:
            raise SystemExit(f"{chapter} 不在教程壳的白名单里")
        files = lesson.get("files") or []
        if not files or not files[0].endswith("window.blp"):
            raise SystemExit(f"{path.name} 的文件列表要以 window.blp 开头")
        for rel in files:
            if not (PROJECT_ROOT / rel).is_file():
                raise SystemExit(f"{path.name} 列出的文件不存在：{rel}")
    _guess_shortcuts(answer_counts, longest_hits, longest_total)


def _guess_shortcuts(answer_counts: dict[int, int], longest_hits: int, longest_total: int) -> None:
    total = sum(answer_counts.values())
    for position, count in sorted(answer_counts.items()):
        if total >= 20 and count / total > 0.4:
            raise SystemExit(f"全课 {total} 题里有 {count} 题答案在第 {position + 1} 个选项，位置太集中，重排选项")
    if total >= 20 and longest_hits / longest_total > 0.5:
        raise SystemExit(f"全课 {longest_total} 题里有 {longest_hits} 题的正确项独占最长（并列不算），补长干扰项或缩短正确项")


def check_exercises() -> None:
    print("== 章节子程序 ==", flush=True)
    for chapter in CHAPTERS:
        root = PROJECT_ROOT / "exercise" / chapter
        required = [
            root / "meson.build",
            root / "cube.cc",
            root / "cube.hh",
            root / "cube_test.cc",
            root / "view.cc",
            root / "view.hh",
            root / "session.cc",
            root / "session.hh",
            root / "ui" / "main.cc",
            root / "ui" / "window.blp",
            root / "ui" / "style.css",
            root / "ui" / "app.gresource.xml",
            root / "compat" / "glib_final_type_shim.h",
        ]
        missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
        if missing:
            raise SystemExit(f"{chapter} 缺 " + ", ".join(missing))
        if "NON_UNIQUE" not in (root / "ui" / "main.cc").read_text(encoding="utf-8"):
            raise SystemExit(f"exercise/{chapter}/ui/main.cc 要标 NON_UNIQUE，几章的窗口才能同时开")
        number = chapter[:2]
        meson = (root / "meson.build").read_text(encoding="utf-8")
        if f"executable('cube-{number}'" not in meson:
            raise SystemExit(f"exercise/{chapter}/meson.build 要编出 cube-{number}")
        rust = (PROJECT_ROOT / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
        if f'("{chapter}", "cube-{number}")' not in rust:
            raise SystemExit(f"教程壳的白名单里要有 (\"{chapter}\", \"cube-{number}\")")


def check_models() -> None:
    """魔方模型两份实现的一致性，和讲解里每张回放图。用 Node 直接跑 .ts（22.6+）。"""
    print("== 魔方模型与讲解回放图 ==", flush=True)
    node = tool("node")
    for script in ("check_model.ts", "check_content_cubes.ts"):
        completed = subprocess.run([node, str(PROJECT_ROOT / "scripts" / script)], cwd=PROJECT_ROOT)
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)
    # C++ 这一份：每章测试里的黄金向量必须和 cube_golden.json 逐条相同。
    golden = json.loads((PROJECT_ROOT / "scripts" / "cube_golden.json").read_text(encoding="utf-8"))
    for chapter in CHAPTERS[1:]:
        text = (PROJECT_ROOT / "exercise" / chapter / "cube_test.cc").read_text(encoding="utf-8")
        for item in golden:
            literal = '{"%s", "%s"}' % (item["alg"], item["state"])
            if literal not in text:
                raise SystemExit(f"{chapter}/cube_test.cc 缺黄金向量 {literal}")


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
    print("== 编译七章 gtkmm 窗口并跑测试 ==", flush=True)
    env = toolchain_env()
    meson = tool("meson", env)
    for chapter in CHAPTERS:
        root = PROJECT_ROOT / "exercise" / chapter
        if not (root / "build" / "build.ninja").is_file():
            run([meson, "setup", "build"], f"{chapter} 配置", env=env, cwd=root)
        run([meson, "compile", "-C", "build"], f"{chapter} 编译", env=env, cwd=root)
        run([meson, "test", "-C", "build"], f"{chapter} 测试", env=env, cwd=root)


def main() -> None:
    _force_utf8_output()
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="追加教程壳的前端构建与 cargo check")
    parser.add_argument("--skip-rust", action="store_true", help="--full 时跳过 cargo")
    parser.add_argument("--native", action="store_true", help="用 meson 编译 exercise/ 下的七个 gtkmm 窗口并跑测试")
    args = parser.parse_args()

    check_app_json()
    check_ports()
    check_content()
    check_exercises()
    check_contract()
    check_models()
    if args.native:
        check_native()
    if args.full or DEFAULT_FULL:
        check_build(args.skip_rust)
    print("OK", flush=True)


if __name__ == "__main__":
    main()
