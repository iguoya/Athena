#!/usr/bin/env python3
"""数学罗盘的验证入口：guide.json 内容结构、id 与端口对账、前端构建、cargo check。

导引是图谱/参考类：没有进度库、没有出处契约、没有跨应用校验（主仓库 ADR 0174）；
机器能拦的是结构错误（悬空引用、id 漂移、launch 命令与 id 不一致），内容质量靠
AGENTS.md 里的核对义务（updated 字段）与评审。

用法：
    python3 scripts/check.py               # 全部检查
    python3 scripts/check.py --skip-rust   # 跳过 cargo check
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "content" / "guide.json"
APP_JSON = ROOT / "app.json"
EXPECTED_ID = "mathematics-compass"
EXPECTED_PORT = 1523
ERRORS: list[str] = []


def fail(msg: str) -> None:
    ERRORS.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"{path.relative_to(ROOT)}: {e}")
        return None


def nonempty(guide: dict, *keys: str, where: str) -> None:
    for k in keys:
        v = guide.get(k)
        if not (isinstance(v, str) and v.strip()):
            fail(f"{where}: 字段 {k} 不能为空")


def check_identity() -> None:
    app = load(APP_JSON)
    if not app:
        return
    if app.get("id") != EXPECTED_ID:
        fail(f"app.json: id 应为 {EXPECTED_ID}，实际 {app.get('id')!r}")
    dev = app.get("dev", {})
    port = str(dev.get("ready", {}).get("http", "")).rsplit(":", 1)[-1]
    if port != str(EXPECTED_PORT):
        fail(f"app.json: dev.ready.http 端口应为 {EXPECTED_PORT}，实际 {port!r}")
    if dev.get("binary") != f"athena-{EXPECTED_ID}":
        fail(f"app.json: dev.binary 应为 athena-{EXPECTED_ID}")
    if "progress" in app:
        fail("app.json: 图谱/参考类不建进度库，不应有 progress 声明")
    for needle, path in [
        (str(EXPECTED_PORT), ROOT / "vite.config.ts"),
        (str(EXPECTED_PORT), ROOT / "src-tauri" / "tauri.conf.json"),
    ]:
        if needle not in path.read_text(encoding="utf-8"):
            fail(f"{path.relative_to(ROOT)}: 找不到端口 {EXPECTED_PORT}（三处必须一致）")


def check_guide() -> dict:
    guide = load(GUIDE)
    if not guide:
        return {}
    where = "content/guide.json"
    if guide.get("schema") != 1:
        fail(f"{where}: schema 应为 1")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(guide.get("updated", ""))):
        fail(f"{where}: updated 必须是 YYYY-MM-DD")
    nonempty(guide, "mainline", where=where)

    ov = guide.get("overview", {})
    nonempty(ov, "claim", where=f"{where} overview")
    for key in ("paragraphs", "howto"):
        if not ov.get(key) or not all(isinstance(s, str) and s.strip() for s in ov[key]):
            fail(f"{where} overview.{key} 必须是非空字符串数组")

    nodes = guide.get("nodes", [])
    node_ids = [n.get("id") for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        fail(f"{where}: 节点 id 重复")
    for n in nodes:
        nid = n.get("id", "?")
        w = f"{where} 节点 {nid}"
        if not re.fullmatch(r"[a-z0-9-]+", str(nid)):
            fail(f"{w}: id 只允许小写字母数字与连字符")
        if n.get("launch") != f"launcher open {nid}":
            fail(f"{w}: launch 必须是 'launcher open {nid}'（跨应用只走启动命令，不引用路径）")
        nonempty(n, "title", "kind", "source", "purpose", "tradeoff", "timeHint", where=w)
        pts = n.get("points", [])
        if len(pts) < 3:
            fail(f"{w}: 掌握要点至少 3 条")
        for pt in pts:
            if not (isinstance(pt.get("point"), str) and pt["point"].strip()) or not (
                isinstance(pt.get("detail"), str) and pt["detail"].strip()
            ):
                fail(f"{w}: 每条要点都要有 point 与 detail")
        if not n.get("milestones") or not all(isinstance(s, str) and s.strip() for s in n["milestones"]):
            fail(f"{w}: milestones 必须是非空字符串数组")

    stages = guide.get("stages", [])
    stage_nodes = [s.get("node") for s in stages]
    if len({s.get("id") for s in stages}) != len(stages):
        fail(f"{where}: 站 id 重复")
    for s in stages:
        w = f"{where} 阶段 {s.get('id', '?')}"
        nonempty(s, "name", "claim", where=w)
        if not s.get("why") or not all(isinstance(x, str) and x.strip() for x in s["why"]):
            fail(f"{w}: why 必须是非空字符串数组")
        if s.get("node") not in node_ids:
            fail(f"{w}: 引用的节点 {s.get('node')!r} 不存在")
    graph = guide.get("graph", {})
    if graph.get("order") != stage_nodes:
        fail(f"{where}: graph.order 必须与 stages 的节点顺序一致（顺序图就是主线的渲染）")
    for tid in graph.get("tools", []):
        if tid not in node_ids:
            fail(f"{where}: graph.tools 引用的 {tid!r} 不在节点里")

    for c in guide.get("companions", []):
        w = f"{where} companion {c.get('id', '?')}"
        if c.get("id") in node_ids:
            fail(f"{w}: 只提及不占节点，id 不得与路线节点重复")
        if c.get("launch") != f"launcher open {c.get('id')}":
            fail(f"{w}: launch 必须是 'launcher open {c['id']}'")
        nonempty(c, "title", "note", where=w)

    books = guide.get("books", {})
    nonempty(books, "default", "single", "backtrack", where=f"{where} books")
    if not books.get("compare"):
        fail(f"{where} books.compare 不能为空")
    gap = guide.get("gap", {})
    nonempty(gap, "claim", where=f"{where} gap")
    if not gap.get("essay") or not all(isinstance(s, str) and s.strip() for s in gap["essay"]):
        fail(f"{where} gap.essay 必须是非空字符串数组")

    blob = GUIDE.read_text(encoding="utf-8")
    for banned in ("TODO", "待补", "占位", "FIXME"):
        if banned in blob:
            fail(f"{where}: 出现 {banned!r}——导引不留占位（ADR 0129）")

    print(f"路线 {len(stages)} 站 {len(nodes)} 节点，工具 {len(graph.get('tools', []))} 个，提及 {len(guide.get('companions', []))} 个")
    return guide


def run(cmd: list[str], step: str, cwd: Path = ROOT) -> None:
    print(f"== {step}")
    exe = shutil.which(cmd[0])
    if exe is None:
        fail(f"{step}: 找不到 {cmd[0]}")
        return
    r = subprocess.run([exe, *cmd[1:]], cwd=cwd)
    if r.returncode != 0:
        fail(f"{step} 失败")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-rust", action="store_true")
    args = ap.parse_args()
    check_identity()
    check_guide()
    if not ERRORS:
        if not (ROOT / "node_modules").is_dir():
            run(["pnpm", "install"], "安装前端依赖")
        run(["pnpm", "run", "build"], "前端构建")
        if not args.skip_rust:
            run(["cargo", "check", "-p", "athena-mathematics-compass"], "cargo check")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
