#!/usr/bin/env python3
"""驾考学习应用的验证入口：内容 JSON、出处合约由仓库根检查，这里跑分析与测试。

用 Python 而不是 shell（ADR 0047）。

用法：
    python3 scripts/check.py
    python3 scripts/check.py --skip-build
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def flutter_bin() -> str:
    found = shutil.which("flutter")
    if found:
        return found
    name = "flutter.bat" if os.name == "nt" else "flutter"
    candidate = Path.home() / "flutter" / "bin" / name
    if candidate.is_file():
        return str(candidate)
    raise SystemExit("找不到 flutter。把 SDK 放进 PATH，或安装到 ~/flutter。")


def flutter_env() -> dict[str, str]:
    env = os.environ.copy()
    if sys.platform == "darwin":
        developer = Path("/Applications/Xcode.app/Contents/Developer")
        if (developer / "usr/bin/xcodebuild").is_file():
            env.setdefault("DEVELOPER_DIR", str(developer))
            xcode_bin = str(developer / "usr/bin")
            env["PATH"] = xcode_bin + os.pathsep + env.get("PATH", "")
    return env


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT, env=flutter_env())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def check_json() -> None:
    print("== 内容 JSON 校验 ==", flush=True)
    files = sorted((PROJECT_ROOT / "content").rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有任何 JSON")
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error
    print(f"{len(files)} 个 JSON 文件解析通过", flush=True)


def check_cheat_images() -> None:
    """速记页内容里每个 `image` 都得指到真实存在的文件，且在 pubspec 的 assets 目录内
    （ADR 0080）：发行包走 assets，开发读磁盘，路径写错只会在运行时静默退回自绘图。"""
    print("== 速记页规范图校验 ==", flush=True)
    content = PROJECT_ROOT / "content"
    assets = [
        line.strip()[2:].strip()
        for line in (PROJECT_ROOT / "pubspec.yaml").read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- content/images/")
    ]
    problems: list[str] = []
    count = 0
    for name, key in (("signs", "signs"), ("markings", "markings"), ("gauges", "gauges"), ("gestures", "gestures")):
        data = json.loads((content / f"{name}.json").read_text(encoding="utf-8"))
        for item in data[key]:
            image = item.get("image")
            if not image:
                continue
            count += 1
            if not (content / image).is_file():
                problems.append(f"{name}.json {item['id']}: 文件不存在 {image}")
            elif not any(f"content/{image}".startswith(prefix) for prefix in assets):
                problems.append(f"{name}.json {item['id']}: {image} 不在 pubspec 的 assets 目录里")
    if problems:
        raise SystemExit("\n".join(problems))
    print(f"{count} 张规范图都存在且已列入 assets", flush=True)


def _load_questions() -> list[dict]:
    questions: list[dict] = []
    for path in sorted((PROJECT_ROOT / "content" / "questions").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("questions", [])
        questions.extend(item for item in items if isinstance(item, dict) and "choices" in item)
    return questions


def check_recall_coverage() -> None:
    """速记页每个条目都得有相关题（ADR 0089）：自测「认得」以作答记录为准（ADR 0083），
    没有相关题的条目只能退回自测作答、无从取证。当初的 11 个豁免已经清零——条目里有的
    概念，题库就该有题可考；这条检查挡住「新增条目悄悄掉队」。"""
    print("== 速记条目相关题覆盖校验 ==", flush=True)
    import re

    content = PROJECT_ROOT / "content"
    questions = _load_questions()
    sign_of = {q.get("sign") or q.get("sign_ref") for q in questions if q.get("sign") or q.get("sign_ref")}
    marking_of = {q["marking"] for q in questions if q.get("marking")}
    problems: list[str] = []

    for name, key, tagged in (
        ("signs", "signs", sign_of),
        ("markings", "markings", marking_of),
    ):
        data = json.loads((content / f"{name}.json").read_text(encoding="utf-8"))[key]
        for item in data:
            if item["id"] not in tagged:
                problems.append(f"{name}.json {item['id']}（{item['name']}）: 没有题目标注这个条目")
    for name, key in (("gauges", "gauges"), ("gestures", "gestures")):
        data = json.loads((content / f"{name}.json").read_text(encoding="utf-8"))[key]
        for item in data:
            if not item.get("questions"):
                problems.append(f"{name}.json {item['id']}（{item['name']}）: questions 为空")
    for name, key in (("cheatsheet", "groups"), ("notes", "groups")):
        data = json.loads((content / f"{name}.json").read_text(encoding="utf-8"))[key]
        for group in data:
            pattern = re.compile(group["match"])
            hits = [
                q
                for q in questions
                if pattern.search(q.get("prompt", ""))
                or any(pattern.search(choice.get("label", "")) for choice in q["choices"])
            ]
            if not hits:
                problems.append(f"{name}.json {group['id']}（{group['title']}）: 正则匹配不到任何题")
    # 专题的要点组按科目取题（ADR 0097、0103）：每个标明的科目都得有相关题；条目的出处必须在 catalog 里。
    catalog = json.loads((content / "sources" / "catalog.json").read_text(encoding="utf-8"))
    source_ids = {item["id"] for item in catalog["sources"]}
    prefix = {"subject1": "drive.s1.", "subject4": "drive.s4."}
    for path in sorted((content / "topics").glob("*.json")):
        for group in json.loads(path.read_text(encoding="utf-8"))["groups"]:
            pattern = re.compile(group["match"])
            for subject in group["subjects"]:
                hits = [
                    q
                    for q in questions
                    if q["id"].startswith(prefix[subject])
                    and (
                        pattern.search(q.get("prompt", ""))
                        or any(pattern.search(choice.get("label", "")) for choice in q["choices"])
                    )
                ]
                if not hits:
                    problems.append(f"topics/{path.name} {group['id']}: 正则在 {subject} 里匹配不到任何题")
            for entry in group["items"]:
                if entry["source_id"] not in source_ids:
                    problems.append(f"topics/{path.name} {group['id']}: 出处 {entry['source_id']} 不在 catalog")
                if not entry.get("locator"):
                    problems.append(f"topics/{path.name} {group['id']}: 「{entry['scenario']}」没有条款定位")
    if problems:
        raise SystemExit("\n".join(problems))
    print(
        f"{len(questions)} 道题：标志 {len(sign_of)}、标线 {len(marking_of)} 个条目有题，"
        "仪表、手势、数字组、要点组全部有题",
        flush=True,
    )


def desktop_target() -> str:
    mapping = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}
    system = platform.system()
    if system not in mapping:
        raise SystemExit(f"没有为 {system} 配置桌面构建目标")
    return mapping[system]


def desktop_toolchain_ready(target: str) -> str | None:
    """返回不能构建时的原因；能构建则返回 None。

    macOS 桌面必须用完整 Xcode，只有 Command Line Tools 时 xcodebuild 会在。
    CI 的 macos-15 有 Xcode；本机若还没装，分析与测试仍然要过。
    """
    if target == "macos":
        env = flutter_env()
        xcodebuild = shutil.which("xcodebuild", path=env.get("PATH"))
        if xcodebuild is None:
            return "没有 xcodebuild"
        probe = subprocess.run(
            [xcodebuild, "-version"],
            capture_output=True,
            text=True,
            env=env,
        )
        if probe.returncode != 0:
            return "需要完整 Xcode，当前只有 Command Line Tools"
    return None


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证驾考学习应用")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="只跑分析与测试，不编桌面目标（改内容时够用）",
    )
    arguments = parser.parse_args()

    check_json()
    check_cheat_images()
    check_recall_coverage()
    flutter = flutter_bin()
    run([flutter, "pub", "get"], "安装 Dart 依赖")
    run([flutter, "analyze"], "静态分析")
    # 数据层是本地 SQLite（ADR 0069）：每个测试文件开自己的临时库，
    # 并发互不踩，不再依赖任何外部数据库。
    run([flutter, "test"], "测试")
    if not arguments.skip_build:
        target = desktop_target()
        reason = desktop_toolchain_ready(target)
        if reason:
            print(f"== 跳过构建 {target}：{reason} ==", flush=True)
        else:
            run([flutter, "build", target, "--debug"], f"构建 {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
