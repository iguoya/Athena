#!/usr/bin/env python3
"""贪吃蛇应用的验证入口。

默认只做结构校验：app.json、端口、课表、出处契约、十章程序文件齐备。
CI 没有 raylib，不能把 cmake 编进默认检查。本机要连蛇一起编，加 --native。
--full 追加教程壳的前端构建和 cargo check，仍然不编 raylib。

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

EXPECTED_ID = "snake"
EXPECTED_PORT = 1514
DEFAULT_FULL = False
CHAPTERS = ("01-window", "02-grid", "03-body", "04-input", "05-food", "06-state", "07-score", "08-logic", "09-test", "10-polish")
# 设计篇导读（应用级 ADR 0005）：文件名 11-design，与第 10 章共用同一个程序目录。
DESIGN_LESSON = ("11-design", "10-polish")
LESSONS = [(chapter, chapter) for chapter in CHAPTERS] + [DESIGN_LESSON]
TARGETS = dict(zip(CHAPTERS, (f"snake-{i:02d}" for i in range(1, 11)), strict=True))


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str, env: dict[str, str] | None = None) -> str:
    found = shutil.which(name, path=None if env is None else env.get("PATH"))
    if found is None:
        hint = ""
        if name == "cmake":
            hint = "。Windows 装 Visual Studio C++ 工作负载或 MSYS2 的 cmake 都可以；raylib 不用预装"
        raise SystemExit(f"找不到 {name}，请先安装后重试{hint}")
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
    if not isinstance(sections, list) or len(sections) != len(LESSONS):
        raise SystemExit(f"course.json 必须有 {len(LESSONS)} 节（十章 + 设计篇导读）")
    for section, (stem, chapter) in zip(sections, LESSONS, strict=True):
        sid = section.get("id", "")
        if not sid.startswith("snake."):
            raise SystemExit(f"节 id {sid!r} 必须用 snake. 前缀")
        if section.get("exercise") != chapter:
            raise SystemExit(f"节 {sid} 的 exercise 必须是 {chapter}")
        path = PROJECT_ROOT / "content" / "chapters" / f"{stem}.json"
        lesson = json.loads(path.read_text(encoding="utf-8"))
        if lesson.get("id") != sid:
            raise SystemExit(f"{path.name} 的 id 与课表不一致")
        lesson_sections = lesson.get("sections") or []
        if not any(item.get("role") == "focus" for item in lesson_sections):
            raise SystemExit(f"{path.name} 缺少主程序的重点讲解")
        for item in lesson_sections:
            if item.get("role") == "diagram":
                d = item.get("diagram", "")
                if len(d) < 10 or not any(k in d for k in ("flowchart", "stateDiagram", "sequenceDiagram", "graph ")):
                    raise SystemExit(f"{path.name} 的 diagram 块缺合法的 mermaid 图源")
            if item.get("role") == "code" and len(item.get("code", "")) < 10:
                raise SystemExit(f"{path.name} 的 code 块内容为空")
        questions = lesson.get("questions") or []
        if not questions:
            raise SystemExit(f"{path.name} 没有题目")
        seen: set[str] = set()
        for question in questions:
            qid = question.get("id", "")
            if not qid.startswith("snake.") or qid in seen:
                raise SystemExit(f"{path.name} 的题目 id 不合法：{qid!r}")
            seen.add(qid)
            if not question.get("stem") or not question.get("choices"):
                raise SystemExit(f"{qid} 缺题干或选项")
            if not question.get("source_refs"):
                raise SystemExit(f"{qid} 缺 source_refs")
        runs = lesson.get("runs") or []
        if len(runs) != 1 or runs[0].get("id") != chapter:
            raise SystemExit(f"{path.name} 要且只要一个运行 id：{chapter}")
        rust = (PROJECT_ROOT / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
        for run in runs:
            if f'"{run["id"]}"' not in rust:
                raise SystemExit(f"{run['id']} 不在教程壳的白名单里")
        lesson_files = lesson.get("files") or []
        # 设计篇导读以设计总览打头，其余各章以主程序打头。
        lead_file = "docs/design/overview.md" if stem == DESIGN_LESSON[0] else "src/main.cc"
        if not lesson_files or not lesson_files[0].endswith(lead_file):
            raise SystemExit(f"{path.name} 的文件列表要以 {lead_file} 开头")
        for rel in lesson_files:
            if not (PROJECT_ROOT / rel).is_file():
                raise SystemExit(f"{path.name} 列出的文件不存在：{rel}")


def check_exercises() -> None:
    print("== 章节子程序 ==", flush=True)
    for chapter in CHAPTERS:
        root = PROJECT_ROOT / "exercise" / chapter
        required = [root / "CMakeLists.txt", root / "src" / "main.cc"]
        missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
        if missing:
            raise SystemExit(f"{chapter} 缺 " + ", ".join(missing))
        main = root / "src" / "main.cc"
        text = main.read_text(encoding="utf-8")
        if "EndDrawing" not in text or "GetFrameTime" not in text:
            raise SystemExit(f"{main.relative_to(PROJECT_ROOT)} 里要有游戏循环（EndDrawing + GetFrameTime）")
        if f"project({TARGETS[chapter]}" not in (root / "CMakeLists.txt").read_text(encoding="utf-8"):
            raise SystemExit(f"{chapter} 的 CMakeLists.txt 项目名要与 {TARGETS[chapter]} 对应")
    logic = PROJECT_ROOT / "exercise" / "08-logic" / "logic.hh"
    test = PROJECT_ROOT / "exercise" / "09-test" / "tests" / "logic_test.cc"
    if not logic.is_file():
        raise SystemExit("08-logic 缺 logic.hh")
    if not test.is_file():
        raise SystemExit("09-test 缺 tests/logic_test.cc")
    polish = PROJECT_ROOT / "exercise" / "10-polish"
    if not (polish / "logic.hh").is_file() or not (polish / "tests" / "logic_test.cc").is_file():
        raise SystemExit("10-polish 缺 logic.hh 或 tests/logic_test.cc")


# 注释里提到 raylib 是正常的，只拦 #include。
RAYLIB_INCLUDE = re.compile(r'#\s*include\s*[<"][^>"]*raylib', re.IGNORECASE)


def _between(text: str, begin: str, end: str, what: str) -> str:
    start = text.find(begin)
    stop = text.find(end)
    if start < 0 or stop < start:
        raise SystemExit(f"docs/design/overview.md 缺 {what} 的标记 {begin} … {end}")
    return text[start + len(begin):stop]


def check_design() -> None:
    """设计总览与代码不漂移（应用级 ADR 0005）。静态检查，不编译。"""
    print("== 设计总览与追溯矩阵 ==", flush=True)
    polish = PROJECT_ROOT / "exercise" / "10-polish"
    overview_path = PROJECT_ROOT / "docs" / "design" / "overview.md"
    if not overview_path.is_file():
        raise SystemExit("缺 docs/design/overview.md")
    overview = overview_path.read_text(encoding="utf-8")

    # 追溯矩阵：第一列编号，第三列验证方式。
    rows: dict[str, str] = {}
    for line in _between(overview, "<!-- trace:begin -->", "<!-- trace:end -->", "追溯矩阵").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"N?FR-\d+", cells[0]):
            if cells[2] not in ("测试", "人工", "未覆盖"):
                raise SystemExit(f"追溯矩阵 {cells[0]} 的验证方式必须是 测试 / 人工 / 未覆盖，现为 {cells[2]!r}")
            rows[cells[0]] = cells[2]
    if not rows:
        raise SystemExit("追溯矩阵里没有读到任何需求行")

    # 需求表里出现的编号都要进矩阵，反过来也一样。
    declared = set(re.findall(r"^\| (N?FR-\d+) \|", overview, flags=re.MULTILINE))
    if declared != set(rows):
        raise SystemExit(f"需求表与追溯矩阵的编号不一致：{sorted(declared ^ set(rows))}")

    # 测试里的 @covers 标记。
    covered: set[str] = set()
    for test in sorted((polish / "tests").glob("*.cc")):
        text = test.read_text(encoding="utf-8")
        if RAYLIB_INCLUDE.search(text):
            raise SystemExit(f"{test.relative_to(PROJECT_ROOT)} 不得包含 raylib 头文件（NFR-1）")
        for match in re.finditer(r"@covers\s+([A-Z0-9, -]+)", text):
            covered.update(re.findall(r"N?FR-\d+", match.group(1)))
    unknown = covered - set(rows)
    if unknown:
        raise SystemExit(f"测试里的 @covers 引用了矩阵里没有的编号：{sorted(unknown)}")
    missing = sorted(rid for rid, how in rows.items() if how == "测试" and rid not in covered)
    if missing:
        raise SystemExit(f"追溯矩阵标「测试」但没有任何 @covers 标记的用例：{missing}")
    manual = sorted(rid for rid, how in rows.items() if how != "测试" and rid in covered)
    if manual:
        raise SystemExit(f"测试已经覆盖却没有在矩阵里标「测试」：{manual}")

    # 接口表里的函数都要在 logic.hh 里。
    logic = (polish / "logic.hh").read_text(encoding="utf-8")
    if RAYLIB_INCLUDE.search(logic):
        raise SystemExit("exercise/10-polish/logic.hh 不得包含 raylib 头文件（NFR-1）")
    names = re.findall(r"^\| `(\w+)` \|", _between(overview, "<!-- api:begin -->", "<!-- api:end -->", "接口表"), flags=re.MULTILINE)
    if not names:
        raise SystemExit("接口表里没有读到任何函数名")
    absent = [name for name in names if not re.search(rf"\b{name}\b", logic)]
    if absent:
        raise SystemExit(f"接口表里的函数在 logic.hh 中找不到：{absent}")


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
    print("== 编译十个 raylib 程序 ==", flush=True)
    env = toolchain_env()
    cmake = tool("cmake", env)
    cache = PROJECT_ROOT / ".cache" / "fetchcontent"
    cache.mkdir(parents=True, exist_ok=True)
    cache_arg = f"-DFETCHCONTENT_BASE_DIR={cache}"
    for chapter in CHAPTERS:
        root = PROJECT_ROOT / "exercise" / chapter
        run([cmake, "-B", "build", cache_arg], f"{chapter} 配置", env=env, cwd=root)
        run([cmake, "--build", "build"], f"{chapter} 编译", env=env, cwd=root)
        exe = root / "build" / (TARGETS[chapter] + (".exe" if os.name == "nt" else ""))
        if not exe.is_file():
            raise SystemExit(f"{chapter} 编译过了但没有找到 {exe.name}")
    ctest = tool("ctest", env)
    for chapter in ("09-test", "10-polish"):
        rules = PROJECT_ROOT / "exercise" / chapter
        # 多配置生成器（VS）按配置名挑测试命令；单配置生成器忽略 -C，写了也无害。
        ctest_cmd = [ctest, "--test-dir", "build", "--output-on-failure"]
        if os.name == "nt":
            ctest_cmd += ["-C", "Debug"]
        run(ctest_cmd, f"{chapter} 规则测试", env=env, cwd=rules)


def main() -> None:
    _force_utf8_output()
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="追加教程壳的前端构建与 cargo check")
    parser.add_argument("--skip-rust", action="store_true", help="--full 时跳过 cargo")
    parser.add_argument("--native", action="store_true", help="用 cmake 编译 exercise/ 下的十个 raylib 程序")
    args = parser.parse_args()

    check_app_json()
    check_ports()
    check_content()
    check_exercises()
    check_design()
    check_contract()
    if args.native:
        check_native()
    if args.full or DEFAULT_FULL:
        check_build(args.skip_rust)
    print("OK", flush=True)


if __name__ == "__main__":
    main()
