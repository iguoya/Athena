#!/usr/bin/env python3
"""高等数学（工本）应用的验证入口：内容一致性、判分出处、前端构建、Rust 侧检查。

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
CONTENT = PROJECT_ROOT / "content"


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


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error


def check_content() -> None:
    """内容校验：JSON 合法、引用一致、判分块出处必带（exam 档）。"""
    print("== 内容校验 ==", flush=True)
    files = sorted(CONTENT.rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有任何 JSON，内容目录是不是错了？")

    curriculum = load_json(CONTENT / "curriculum.json")
    knowledge = load_json(CONTENT / "knowledge.json")
    known_ids = {k["id"] for k in knowledge["knowledge"]}

    # 课表引用的知识点必须存在；节必须有对应的内容文件
    section_ids: set[str] = set()
    for chapter in curriculum["chapters"]:
        for section in chapter.get("sections", []):
            section_ids.add(section["id"])
            for kid in section.get("knowledge", []):
                if kid not in known_ids:
                    raise SystemExit(f"课表 {chapter['id']}/{section['id']} 引用了未知知识点 {kid}")

    # 知识点：requires 指向存在的 ID；难度与目标两维齐全；教材/考纲坐标必填
    for k in knowledge["knowledge"]:
        for req in k.get("requires", []):
            if req not in known_ids:
                raise SystemExit(f"知识点 {k['id']} 的先修 {req} 不存在")
        for field in ("difficulty", "target", "textbook_ref", "syllabus_ref"):
            if not k.get(field):
                raise SystemExit(f"知识点 {k['id']} 缺 {field}")

    # 节内容文件：id 对得上、判分块出处必带、数值答案可复核
    section_files = list((CONTENT / "sections").glob("*.json"))
    if not section_files:
        raise SystemExit("content/sections/ 下没有任何节内容")
    for path in sorted(section_files):
        data = load_json(path)
        if data["id"] not in section_ids:
            raise SystemExit(f"{path.name}: 节 {data['id']} 不在课表里（课表只登记已写的节）")
        for block in data["blocks"]:
            kind = block.get("kind")
            if kind in ("exercise", "retrieval"):
                refs = block.get("source_refs") or []
                if not refs:
                    raise SystemExit(
                        f"{path.name}: 判分块 {block.get('id')} 缺 source_refs（exam 档阻断）"
                    )
                for ref in refs:
                    if ref.get("relation") not in ("verbatim", "adapted", "authored"):
                        raise SystemExit(
                            f"{path.name}: {block.get('id')} 的 relation 非法：{ref.get('relation')}"
                        )
                    if ref["relation"] in ("verbatim", "adapted") and not ref.get("locator"):
                        raise SystemExit(f"{path.name}: {block.get('id')} 的 {ref['relation']} 缺 locator")
                if kind == "exercise":
                    answer = block.get("answer", {})
                    if answer.get("type") not in ("choice", "numeric"):
                        raise SystemExit(f"{path.name}: {block.get('id')} 答案类型非法")
                    if answer["type"] == "choice":
                        n = len(answer.get("options", []))
                        if not 0 <= answer.get("correct", -1) < n:
                            raise SystemExit(f"{path.name}: {block.get('id')} 的 correct 越界")
                    for kid in block.get("knowledge", []):
                        if kid not in known_ids:
                            raise SystemExit(f"{path.name}: {block.get('id')} 引用未知知识点 {kid}")

    # 真题整卷：结构合法
    exams_dir = CONTENT / "exams"
    for path in sorted(exams_dir.glob("*.json")):
        data = load_json(path)
        if not data.get("year") or not data.get("items") and not data.get("sections"):
            raise SystemExit(f"{path.name}: 真题整卷缺 year 或题目")
    print(
        f"{len(files)} 个 JSON 文件解析通过；知识点 {len(known_ids)} 个、节 {len(section_files)} 个",
        flush=True,
    )


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    pnpm = tool("pnpm")
    repo_lock = PROJECT_ROOT.parents[1] / "pnpm-lock.yaml"
    if repo_lock.is_file():
        run([pnpm, "install", "--frozen-lockfile"], "安装前端依赖（按 lock）")
    else:
        run([pnpm, "install"], "安装前端依赖")


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证高等数学（工本）应用")
    parser.add_argument(
        "--skip-rust",
        action="store_true",
        help="跳过 Rust 侧检查（只改了内容或前端时用）",
    )
    arguments = parser.parse_args()

    check_content()
    ensure_dependencies()
    # tsc + vite build：类型错误与打包问题一起拦。公式渲染错误运行时降级显示原文，
    # 不在这里拦（提交前人工手算每道判分题是内容层的规矩，见 AGENTS.md）。
    run([tool("pnpm"), "run", "build"], "前端类型检查与构建")

    if not arguments.skip_rust:
        cargo = tool("cargo")
        run(
            [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            "Rust 侧检查",
        )
        run([cargo, "test", "--manifest-path", "src-tauri/Cargo.toml"], "Rust 侧测试")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
