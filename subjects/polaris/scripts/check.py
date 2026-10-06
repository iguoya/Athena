#!/usr/bin/env python3
"""Polaris 的独立验证入口：内容 JSON、原料覆盖、内容契约，再前端构建、单元测试与 Rust 侧检查。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请安装后重试")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def check_json() -> None:
    print("== 内容 JSON 解析 ==", flush=True)
    files = sorted((PROJECT_ROOT / "content").rglob("*.json"))
    if not files:
        raise SystemExit("content/ 下没有 JSON 文件")
    for path in files + [PROJECT_ROOT / "content-contract.json", PROJECT_ROOT / "app.json"]:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error
    print(f"{len(files)} 个内容 JSON 解析通过", flush=True)


def check_absorption() -> None:
    """技术体系图必须完整覆盖导出的原料（ADR 0009 验收清单）。

    原料是 subjects/cpp 首页那张学科路线图的逐字导出。使用者随时会删掉源文件，
    删之前要有把握「信息确实都在 polaris 里了」——靠人眼比对 28 个节点 × 三段
    文字外加 34 条依赖理由是不现实的，所以这件事必须是一项检查。课程知识图谱
    按原图收成计算机 / 电子信息两章（ADR 0010），检查仍按节点 id 对照，不按
    碎片图的旧切分。
    """
    print("== 技术体系图对原料的覆盖 ==", flush=True)
    raw_path = PROJECT_ROOT / "content" / "absorbed" / "cpp-roadmap.json"
    if not raw_path.is_file():
        raise SystemExit(f"缺少原料 {raw_path.relative_to(PROJECT_ROOT)}")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    polaris = json.loads((PROJECT_ROOT / "content" / "polaris.json").read_text(encoding="utf-8"))

    nodes_by_id = {}
    map_of_node = {}
    summaries = {}
    for entry in polaris["maps"]:
        summaries[entry["id"]] = entry.get("summary", "")
        for node in entry["nodes"]:
            nodes_by_id[node["id"]] = node
            map_of_node[node["id"]] = entry["id"]

    # 原料 id -> polaris 节点 id。side 决定前缀，与吸收时的命名规则一致。
    def absorbed_id(raw_node: dict) -> str:
        prefix = "polaris.cs." if raw_node["side"] == "computer" else "polaris.ei."
        return prefix + raw_node["id"]

    problems: list[str] = []

    # 1. 节点在场，且三段正文逐字一致。
    for raw_node in raw["nodes"]:
        node_id = absorbed_id(raw_node)
        node = nodes_by_id.get(node_id)
        if node is None:
            problems.append(f"原料节点 {raw_node['id']} 没有对应的 {node_id}")
            continue
        for raw_field, field in (
            ("content", "stable_definition"),
            ("purpose", "engineering_role"),
            ("difficulty", "pitfall"),
        ):
            if raw_node[raw_field] and node.get(field) != raw_node[raw_field]:
                problems.append(
                    f"{node_id} 的 {field} 与原料 {raw_field} 不一致（原料应原文照搬）"
                )

    # 2. 每条依赖的理由都要落在某条边上：同图内走 edges，跨图走 cross_edges。
    rationales = set()
    for entry in polaris["maps"]:
        for edge in entry.get("edges", []):
            rationales.add(edge.get("rationale", ""))
    for edge in polaris.get("cross_edges", []):
        rationales.add(edge.get("rationale", ""))
    for raw_node in raw["nodes"]:
        for prerequisite in raw_node["prerequisites"]:
            if prerequisite["reason"] not in rationales:
                problems.append(
                    f"依赖 {prerequisite['id']} → {raw_node['id']} 的理由没落在任何边上"
                )

    # 3. 理论科目不建节点，但必须在某张图的 theory 里，三段齐全。
    absorbed_theory = {}
    for entry in polaris["maps"]:
        for topic in entry.get("theory", []):
            absorbed_theory[topic["name"]] = topic
    for topic in raw["theory"]:
        landed = absorbed_theory.get(topic["name"])
        if landed is None:
            problems.append(f"理论科目「{topic['name']}」没落在任何一张图里")
            continue
        if landed.get("content") != topic["content"] or landed.get("role") != topic["role"]:
            problems.append(f"理论科目「{topic['name']}」的正文与原料不一致")

    # 4. 推荐入门起点要在所在图的说明里讲明白，否则这条信息只剩一个布尔值。
    for raw_node in raw["nodes"]:
        if not raw_node["entry"]:
            continue
        node_id = absorbed_id(raw_node)
        map_id = map_of_node.get(node_id)
        if map_id and "起点" not in summaries.get(map_id, ""):
            problems.append(
                f"{node_id} 是推荐入门起点，但地图 {map_id} 的 summary 没说明这件事"
            )

    # 5. 课程知识图谱必须是原图那两章，不能再拆回碎片图（ADR 0010）。
    map_ids = {entry["id"] for entry in polaris["maps"]}
    if "computer-science" not in map_ids or "electronic-information" not in map_ids:
        problems.append("课程知识图谱缺少 computer-science / electronic-information 两章")
    for leftover in (
        "computer-programming",
        "computer-machine",
        "computer-network-intelligence",
        "electronic-circuit",
        "electronic-mcu",
        "electronic-embedded",
    ):
        if leftover in map_ids:
            problems.append(f"碎片图 {leftover} 还在，课程节点应已迁入两章")

    if problems:
        for problem in problems:
            print(f"  · {problem}", flush=True)
        raise SystemExit(f"技术体系图未完整覆盖原料，共 {len(problems)} 处。")

    print(
        f"原料 {len(raw['nodes'])} 个节点、"
        f"{sum(len(n['prerequisites']) for n in raw['nodes'])} 条依赖、"
        f"{len(raw['theory'])} 条理论科目均已覆盖",
        flush=True,
    )


def check_contract() -> None:
    """内容契约（ADR 0015 决策 2）：规则本身和它的反例测试各跑一遍。

    这是内容契约的唯一入口：C++ 的 validateDocument 已随 Qt 版一起删除
    （基线 tag pre-web-polaris），不再被构建；新增规则只改 scripts/contract.py，并在 test_contract.py 里配反例。
    """
    run([sys.executable, str(PROJECT_ROOT / "scripts" / "contract.py")], "内容契约校验")
    run([sys.executable, "-m", "unittest", "discover", "-s", str(PROJECT_ROOT / "scripts"),
         "-p", "test_*.py"], "内容契约反例测试")


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    # 有 lock 就按 lock 装：CI 上每次拿到的依赖要和本地一致。
    npm = tool("npm")
    if (PROJECT_ROOT / "package-lock.json").is_file():
        run([npm, "ci"], "安装前端依赖（按 lock）")
    else:
        run([npm, "install"], "安装前端依赖")


def main() -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="验证 Polaris：内容、前端与壳")
    parser.add_argument(
        "--skip-rust",
        action="store_true",
        help="跳过 Rust 侧检查（只改了内容或前端时用它，能省几分钟）",
    )
    arguments = parser.parse_args()

    check_json()
    check_absorption()
    check_contract()
    ensure_dependencies()
    npm = tool("npm")
    # npm run build = tsc -b + vite build，类型和打包一次过。
    run([npm, "run", "build"], "前端类型检查与构建")
    run([npm, "test"], "前端单元测试与渲染冒烟（布局、视口、路由、全部视图）")
    if not arguments.skip_rust:
        run(
            [tool("cargo"), "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            "Rust 侧检查",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
