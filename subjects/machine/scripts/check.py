#!/usr/bin/env python3
"""C 与机器的验证入口：内容校验、课程图结构校验、CMake 配置与构建。

用 Python 而不是 shell：验证是每天都要跑的环节，不该要求 Windows 上先装
Git Bash 或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py [--build-dir DIR] [--buildtype TYPE]
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
    """把命令名解析成真实路径再执行；which 在三个平台上都按本地规则查找。"""
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
    """课表和习题都是 JSON，坏一个文件应用就起不来。先校验再谈构建。"""
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


# ADR 0005 第 3、5 条：三条线、先修方向、知识点前缀。
TRACK_TOPIC_PREFIX = {"c": "machine.c.", "asm": "machine.asm.", "joint": "machine.joint."}
# 汇编独立章允许依赖的唯一一个 C 章：变量要先有地址，汇编才有东西可指。
ASM_MAY_DEPEND_ON_C = {"Memory"}


def validate_curriculum(data: dict, exercise_ids: set[str]) -> list[str]:
    """课程图结构校验，返回问题列表（空表示通过）。纯函数，便于单独测。"""
    errors: list[str] = []
    track_ids = [t.get("id") for t in data.get("tracks", [])]
    if sorted(track_ids) != sorted(TRACK_TOPIC_PREFIX):
        errors.append(f"tracks 应恰好是 {sorted(TRACK_TOPIC_PREFIX)}，现在是 {sorted(map(str, track_ids))}")

    chapters = data.get("chapters", [])
    by_id: dict[str, dict] = {}
    for chapter in chapters:
        cid = chapter.get("id")
        if cid in by_id:
            errors.append(f"章 id 重复：{cid}")
        by_id[cid] = chapter

    topic_ids: set[str] = set()
    for chapter in chapters:
        cid, track = chapter.get("id"), chapter.get("track")
        if track not in TRACK_TOPIC_PREFIX:
            errors.append(f"{cid}: track「{track}」不在 {sorted(TRACK_TOPIC_PREFIX)} 里")
            continue
        prereqs = chapter.get("prerequisites", [])
        for pre in prereqs:
            if pre not in by_id:
                errors.append(f"{cid}: 先修「{pre}」不存在")
        kinds = {by_id[pre].get("track") for pre in prereqs if pre in by_id}
        if track == "c" and kinds - {"c"}:
            errors.append(f"{cid}: C 独立章只能依赖 C 独立章，现在依赖了 {sorted(kinds - {'c'})} 线")
        if track == "asm":
            for pre in prereqs:
                if pre in by_id and by_id[pre].get("track") == "c" and pre not in ASM_MAY_DEPEND_ON_C:
                    errors.append(f"{cid}: 汇编独立章只可依赖 C 的 {sorted(ASM_MAY_DEPEND_ON_C)}，却依赖了「{pre}」")
                if pre in by_id and by_id[pre].get("track") == "joint":
                    errors.append(f"{cid}: 汇编独立章不得依赖联合章「{pre}」")
        if track == "joint":
            if not {"c", "asm"} <= kinds:
                errors.append(f"{cid}: 联合章必须同时直接依赖 C 独立章和汇编独立章，现在只有 {sorted(kinds)}")
        for topic in chapter.get("topics", []):
            tid = topic.get("id", "")
            topic_ids.add(tid)
            if not tid.startswith(TRACK_TOPIC_PREFIX[track]):
                errors.append(f"{cid}: 知识点 id「{tid}」应以 {TRACK_TOPIC_PREFIX[track]} 开头")
        own = {t.get("id") for t in chapter.get("topics", [])}
        for topic in chapter.get("topics", []):
            for req in topic.get("requires", []):
                if req not in own:
                    errors.append(f"{cid}: 知识点「{topic.get('id')}」的 requires「{req}」不在本章内")

    # 环：Kahn 算法删不完就是有环（应用里的布局会静默丢掉环上的章）。
    indegree = {cid: len([p for p in ch.get("prerequisites", []) if p in by_id]) for cid, ch in by_id.items()}
    ready = [cid for cid, n in indegree.items() if n == 0]
    seen = 0
    while ready:
        cid = ready.pop()
        seen += 1
        for other, ch in by_id.items():
            if cid in ch.get("prerequisites", []):
                indegree[other] -= 1
                if indegree[other] == 0:
                    ready.append(other)
    if seen != len(by_id):
        errors.append("先修关系有环：" + "、".join(sorted(c for c, n in indegree.items() if n > 0)))

    for eid in sorted(exercise_ids - topic_ids):
        errors.append(f"exercises.json 的「{eid}」在课表里找不到对应知识点")
    return errors


def check_curriculum() -> None:
    print("== 课程图结构校验 ==", flush=True)
    content = PROJECT_ROOT / "content"
    data = json.loads((content / "curriculum.json").read_text(encoding="utf-8"))
    exercises = json.loads((content / "exercises.json").read_text(encoding="utf-8"))
    errors = validate_curriculum(data, set(exercises))
    if errors:
        lines = ["课程图校验失败："] + [f"  - {e}" for e in errors]
        raise SystemExit(chr(10).join(lines))
    tracks = {}
    for chapter in data["chapters"]:
        tracks[chapter["track"]] = tracks.get(chapter["track"], 0) + 1
    print(f"{len(data['chapters'])} 章通过：" + "、".join(f"{k} {v}" for k, v in sorted(tracks.items())), flush=True)


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证 C 与机器：内容与课程图校验、配置、构建")
    parser.add_argument("--build-dir", default="build", help="构建目录（默认 build）")
    parser.add_argument(
        "--buildtype",
        default="Debug",
        help="传给 CMake 的 CMAKE_BUILD_TYPE（默认 Debug）",
    )
    arguments = parser.parse_args()

    check_json()
    check_curriculum()
    # 多目标实验：骨架在三个目标都能汇编，观察层没过期（ADR 0006 第 6 条）。需要 clang。
    run([sys.executable, str(PROJECT_ROOT / "scripts" / "lab.py"), "check"], "实验校验（多目标汇编）")

    cmake = tool("cmake")
    configure = [
        cmake,
        "-S",
        ".",
        "-B",
        arguments.build_dir,
        f"-DCMAKE_BUILD_TYPE={arguments.buildtype}",
    ]
    # 有 Ninja 就用 Ninja：Windows 上 CMake 默认挑 Visual Studio，那是多配置
    # 生成器，产物会落在 build/Debug/ 而不是 build/，和 app.json 的
    # `dev.run: build/athena-machine` 对不上。指定单配置生成器，三个平台的布局就一致了。
    if shutil.which("ninja") is not None:
        configure += ["-G", "Ninja"]
    run(configure, "CMake 配置")
    # --config 只有多配置生成器（Visual Studio、Xcode）认，单配置生成器忽略它，
    # 所以三个平台可以共用这一条命令。
    run(
        [cmake, "--build", arguments.build_dir, "--config", arguments.buildtype],
        "构建",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
