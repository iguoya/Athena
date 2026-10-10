#!/usr/bin/env python3
"""设计模式应用的验证入口。

默认依次做：app.json 一致性（id、不挂靠、端口）、端口三方对齐、内容校验
（curriculum.json 的知识点与引用、实验案例与判分、软考专题的原题出处）、出处契约、
实验与代码填空的编译验证、前端构建、Rust 检查。--quick 只做前四项。

用 Python 而不是 shell：验证是每天都要跑的环节，不该要求 Windows 上先装
Git Bash 或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py [--quick] [--skip-rust]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_ID = "design-patterns"
EXPECTED_PORT = 1491


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
    if "parent" in data:
        raise SystemExit("app.json 不得有 parent：本应用在「程序设计」圈，不挂靠（仓库 ADR 0121）")
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
    print("== 内容校验 ==", flush=True)
    content = PROJECT_ROOT / "content"
    for path in sorted(content.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}")

    cur = json.loads((content / "curriculum.json").read_text(encoding="utf-8"))
    catalog = {
        s["id"]
        for s in json.loads((content / "sources.json").read_text(encoding="utf-8"))["sources"]
    }
    problems: list[str] = []
    topic_ids: set[str] = set()
    for ch in cur["chapters"]:
        if ch.get("layer") not in (None, "topic", "extension"):
            problems.append(f"章 {ch['id']} 的 layer 只能是 topic / extension 或不写")
        for t in ch["topics"]:
            tid = t["id"]
            if not tid.startswith("dp."):
                problems.append(f"知识点 {tid!r} 必须用 dp. 前缀（ADR 0097 决策 3 同规）")
            if tid in topic_ids:
                problems.append(f"知识点 id 重复：{tid}（一个 id 只装一个东西，ADR 0054）")
            topic_ids.add(tid)

    for ch in cur["chapters"]:
        chapter_topics = {t["id"] for t in ch["topics"]}
        for t in ch["topics"]:
            for r in t.get("requires", []):
                if r not in topic_ids:
                    problems.append(f"{t['id']} 的先修 {r} 不存在")
            for lab in t.get("labs", []):
                case = content / "cases" / lab["case"] / lab["entrypoint"]
                if not case.is_file():
                    problems.append(f"实验 {lab['id']} 的案例文件不存在：{case.relative_to(PROJECT_ROOT)}")
                elif "TODO(实验)" not in case.read_text(encoding="utf-8"):
                    problems.append(f"实验 {lab['id']} 的骨架没有 TODO(实验) 标记（ADR 0059：给骨架，标出空缺）")
                if not (lab.get("pass") or {}).get("includes"):
                    problems.append(f"实验 {lab['id']} 缺 pass.includes，永远到不了「已完成」")
        items = (ch.get("checkpoint") or {}).get("items", [])
        for i, item in enumerate(items):
            if item.get("covers") not in chapter_topics:
                problems.append(f"章 {ch['id']} 考核第 {i + 1} 题的 covers 不是本章知识点")
            if sum(1 for c in item["choices"] if c.get("ok")) != 1:
                problems.append(f"章 {ch['id']} 考核第 {i + 1} 题必须恰好一个正确选项")
        covers = [i.get("covers") for i in items]
        # 只覆盖一个知识点的考核（如延伸章）无从交错
        for a, b in zip(covers, covers[1:]) if len(set(covers)) > 1 else []:
            if a == b:
                problems.append(f"章 {ch['id']} 考核里 {a} 的题相邻了：同一知识点的题要交错排")
                break

        if ch.get("layer") == "topic":
            problems += check_exam_items(ch, catalog)
        for t in ch["topics"]:
            for b in t["lesson"]["blocks"]:
                if b["type"] == "fillcode":
                    problems += check_fillcode(b, catalog)

    if problems:
        raise SystemExit("内容校验没通过：\n  " + "\n  ".join(problems))


BLANK = re.compile(r"\{\{(\d+)\}\}")


def check_fillcode(b: dict, catalog: set[str]) -> list[str]:
    """代码填空块：空位编号三处一致，出处写到卷与题号，改编要写明改了什么。"""
    found: list[str] = []
    where = f"代码填空 {b.get('id')}"
    in_code = {int(n) for n in BLANK.findall(b["code"])}
    in_after = {int(n) for n in BLANK.findall(b.get("after", ""))}
    in_tpl = {int(n) for n in BLANK.findall(b["template"])}
    declared = {x["n"] for x in b["blanks"]}
    if in_code | in_after != declared:
        found.append(f"{where} 的空位 {sorted(in_code | in_after)} 与答案 {sorted(declared)} 对不上")
    if in_tpl != in_code:
        found.append(f"{where} 的编译模板空位 {sorted(in_tpl)} 与代码空位 {sorted(in_code)} 对不上")
    if any(not x["answers"] for x in b["blanks"]):
        found.append(f"{where} 有空位没有官方答案")
    if not b.get("expect"):
        found.append(f"{where} 缺 expect，代入编译永远判不了对")
    src = b.get("source") or {}
    if src.get("relation") not in ("verbatim", "adapted"):
        found.append(f"{where} 的出处必须是 verbatim 或 adapted")
    if src.get("sourceId") not in catalog:
        found.append(f"{where} 的 sourceId 不在 sources.json 里")
    if not re.search(r"\d{4} 年.*试题", src.get("locator", "")):
        found.append(f"{where} 的 locator 要写到「年份 … 试题 N」")
    if not str(src.get("url", "")).startswith("http"):
        found.append(f"{where} 缺可核对的页面链接 url")
    if src.get("relation") == "adapted" and not src.get("why"):
        found.append(f"{where} 标了 adapted 却没写改了什么")
    return found


def compiler() -> str:
    for name in ("g++", "clang++"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("找不到 g++ 或 clang++：实验与代码填空的编译验证需要本机 C++ 编译器（ADR 0057）")


def compile_and_run(cxx: str, source: str, workdir: Path, name: str) -> tuple[bool, str, str]:
    """编译并运行一段源码，返回（是否编译运行成功、编译诊断、标准输出）。"""
    src = workdir / f"{name}.cpp"
    exe = workdir / f"{name}.exe"
    src.write_text(source, encoding="utf-8")
    c = subprocess.run(
        [cxx, "-std=c++20", "-O0", "-Wall", "-Wextra", "-pthread", "-I", str(PROJECT_ROOT / "content" / "cases" / "_shared"),
         str(src), "-o", str(exe)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if c.returncode != 0:
        return False, c.stderr, ""
    r = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    return r.returncode == 0, c.stderr, r.stdout


def check_runnable() -> None:
    """真编译验证：实验骨架原样零警告且不达标；代码填空代入官方答案通过、空着不通过。"""
    print("== 实验与代码填空的编译验证 ==", flush=True)
    cxx = compiler()
    cur = json.loads((PROJECT_ROOT / "content" / "curriculum.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="dp-check-") as tmp:
        work = Path(tmp)
        for ch in cur["chapters"]:
            for t in ch["topics"]:
                for lab in t.get("labs", []):
                    case = PROJECT_ROOT / "content" / "cases" / lab["case"] / lab["entrypoint"]
                    ok, diag, out = compile_and_run(cxx, case.read_text(encoding="utf-8"), work, lab["case"])
                    if not ok:
                        problems.append(f"实验 {lab['id']} 的骨架原样编译运行失败（ADR 0059）：{diag.strip()[:300]}")
                    elif diag.strip():
                        problems.append(f"实验 {lab['id']} 的骨架有编译警告：{diag.strip()[:300]}")
                    elif all(s in out for s in lab["pass"]["includes"]):
                        problems.append(f"实验 {lab['id']} 的骨架原样就达标了，学习者不用动手")
                for b in t["lesson"]["blocks"]:
                    if b["type"] != "fillcode":
                        continue
                    first = {x["n"]: x["answers"][0] for x in b["blanks"]}
                    filled = BLANK.sub(lambda m: first.get(int(m.group(1)), ""), b["template"])
                    ok, diag, out = compile_and_run(cxx, filled, work, b["id"])
                    if not ok or not all(s in out for s in b["expect"]):
                        problems.append(f"代码填空 {b['id']} 代入官方答案没有通过：{(diag or out).strip()[:300]}")
                    empty = BLANK.sub("", b["template"])
                    ok, _, out = compile_and_run(cxx, empty, work, b["id"] + "_empty")
                    if ok and all(s in out for s in b["expect"]):
                        problems.append(f"代码填空 {b['id']} 空着不填也能通过，判分形同虚设")
    if problems:
        raise SystemExit("编译验证没通过：\n  " + "\n  ".join(problems))


def check_exam_items(chapter: dict, catalog: set[str]) -> list[str]:
    """软考专题里的题必须是真题原题（ADR 0121）：出处是 verbatim、能核对、写到题号。"""
    found: list[str] = []
    quizzes = [
        item
        for t in chapter["topics"]
        for b in t["lesson"]["blocks"]
        if b["type"] == "quiz"
        for item in b["items"]
    ]
    quizzes += (chapter.get("checkpoint") or {}).get("items", [])
    for item in quizzes:
        src = item.get("source")
        where = f"软考专题「{item['stem'][:24]}…」"
        if not isinstance(src, dict) or src.get("relation") != "verbatim":
            found.append(f"{where} 不是标了 verbatim 的真题原题")
            continue
        if src.get("sourceId") not in catalog:
            found.append(f"{where} 的 sourceId 不在 sources.json 里")
        if not re.search(r"\d{4} 年.*第 \d+ 题", src.get("locator", "")):
            found.append(f"{where} 的 locator 要写到「年份 … 第 N 题」")
        if not str(src.get("url", "")).startswith("http"):
            found.append(f"{where} 缺可核对的页面链接 url")
    return found


def check_contract() -> None:
    print("== 出处契约 ==", flush=True)
    contract = json.loads(
        (PROJECT_ROOT / "content-contract.json").read_text(encoding="utf-8")
    )
    if contract.get("tier") != "open":
        raise SystemExit("content-contract.json 的 tier 必须是 open（仓库 ADR 0089、0121）")
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
        run([cargo, "check", "--manifest-path", str(PROJECT_ROOT / "src-tauri" / "Cargo.toml")], "Rust cargo check")


def main() -> None:
    _force_utf8_output()
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="只做结构与内容校验，不构建")
    parser.add_argument("--skip-rust", action="store_true", help="跳过 cargo check")
    # --full 是骨架阶段的旧参数：现在默认就是完整检查，保留它免得旧命令报错
    parser.add_argument("--full", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    check_app_json()
    check_ports()
    check_content()
    check_contract()
    if not args.quick:
        check_runnable()
        check_build(args.skip_rust)
    print("OK", flush=True)


if __name__ == "__main__":
    main()
