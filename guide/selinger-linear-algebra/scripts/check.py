#!/usr/bin/env python3
"""Selinger 线性代数精读的验证入口：内容结构、译文与原文公式一致、核对点、出处契约、构建。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash（主仓库 ADR 0047）。

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
CONTENT = ROOT / "content"
ERRORS: list[str] = []


def fail(msg: str) -> None:
    ERRORS.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"{path.relative_to(ROOT)}: {e}")
        return None


def inline_math(s: str) -> list[str]:
    """与 src/inline.ts 的 splitInline 同一规则：收尾的 $ 必须在花括号深度 0。"""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "$":
            k, depth = i + 1, 0
            while k < len(s):
                if s[k] == "\\":
                    k += 2
                    continue
                if s[k] == "{":
                    depth += 1
                elif s[k] == "}":
                    depth -= 1
                elif s[k] == "$" and depth <= 0:
                    break
                k += 1
            if k < len(s):
                out.append(re.sub(r"\s+", " ", s[i + 1 : k]).strip())
                i = k + 1
                continue
        i += 1
    return out


def units(blocks):
    for b in blocks:
        for key in ("t", "title", "caption"):
            if isinstance(b.get(key), dict) and "sha" in b[key]:
                yield b[key]
        if "blocks" in b:
            yield from units(b["blocks"])
        if b.get("k") == "list":
            for it in b["items"]:
                yield from units(it)
        if b.get("k") == "table":
            for row in b.get("rows", []):
                for c in row:
                    if isinstance(c, dict):
                        yield c


def check_structure() -> dict:
    scope = load(CONTENT / "scope.json")
    cur = load(CONTENT / "curriculum.json")
    if not scope or not cur:
        return {}
    pages = [it["id"] for ch in scope["chapters"] for it in ch["items"] if it["page"]]
    ids = set()
    for pid in pages:
        if pid in ids:
            fail(f"scope.json: 节 {pid} 重复")
        ids.add(pid)
        if not (CONTENT / "sections" / f"{pid}.json").is_file():
            fail(f"缺少快照 content/sections/{pid}.json（跑 sync_upstream.py）")
    extra = {p.stem for p in (CONTENT / "sections").glob("*.json")} - ids
    for e in sorted(extra):
        fail(f"快照 {e}.json 不在 scope.json 里（被裁掉的节不留快照）")
    cur_ids = {it["id"] for ch in cur["chapters"] for it in ch["items"] if it["page"]}
    if cur_ids != ids:
        fail("curriculum.json 与 scope.json 不一致（它是生成物，跑 sync_upstream.py）")
    print(f"课表 {len(scope['chapters'])} 章 {len(pages)} 节")
    return {pid: load(CONTENT / "sections" / f"{pid}.json") for pid in pages if (CONTENT / "sections" / f"{pid}.json").is_file()}


def check_translations(sections: dict) -> None:
    total = done = 0
    for pid, data in sections.items():
        if not data:
            continue
        us = list(units(data["blocks"])) + [u for ex in data["exercises"] for u in units(ex["stem"] + ex["sol"])]
        for u in us:
            total += 1
            if not u.get("zh"):
                continue
            done += 1
            # 译文只许改公式外的文字：公式集合必须与原文一致
            if sorted(inline_math(u["zh"])) != sorted(inline_math(u["en"])):
                fail(f"{pid}: 译文公式与原文不一致\n    en: {u['en'][:90]}\n    zh: {u['zh'][:90]}")
        for ex in data["exercises"]:
            if not ex.get("source_refs"):
                fail(f"{pid}.{ex['id']}: 习题缺出处")
    print(f"可译单元 {total}，已译 {done}（{done * 100 // max(total, 1)}%）")


def check_checks(sections: dict) -> None:
    n = 0
    d = CONTENT / "checks"
    if not d.is_dir():
        return
    for p in sorted(d.glob("*.json")):
        data = load(p)
        sec = sections.get(p.stem)
        if data is None:
            continue
        if sec is None:
            fail(f"checks/{p.name}: 没有对应的节")
            continue
        ex_ids = {e["id"] for e in sec["exercises"]}
        for eid, c in data.items():
            n += 1
            if eid not in ex_ids:
                fail(f"checks/{p.name}: 习题 {eid} 不存在")
                continue
            if c.get("kind") == "numbers":
                if not c.get("answer") or not all(isinstance(x, (int, float)) for x in c["answer"]):
                    fail(f"checks/{p.name}:{eid}: numbers 的 answer 必须是非空数字数组")
            elif c.get("kind") == "choice":
                opts = c.get("options", [])
                if len(opts) < 2 or sum(1 for o in opts if o.get("ok")) != 1 or any(not o.get("why") for o in opts):
                    fail(f"checks/{p.name}:{eid}: choice 需要 ≥2 个选项、恰好 1 个 ok，且每项都有 why")
            else:
                fail(f"checks/{p.name}:{eid}: 未知 kind {c.get('kind')!r}")
    print(f"核对点 {n} 道")


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
    sections = check_structure()
    check_translations(sections)
    check_checks(sections)
    if (ROOT / "upstream" / "linear-algebra").is_dir():
        run([sys.executable, "scripts/sync_upstream.py", "--check"], "快照与上游一致性")
    else:
        print("（没有 upstream/ 克隆，跳过快照与上游的一致性检查）")
    for need in ("docs/COVERAGE.md", "docs/LICENSE-NOTICE.md"):
        if not (ROOT / need).is_file():
            fail(f"缺少 {need}")
    if not ERRORS:
        if not (ROOT / "node_modules").is_dir():
            run(["pnpm", "install"], "安装前端依赖")
        run(["pnpm", "run", "build"], "公式自检 + 前端构建")
        if not args.skip_rust:
            run(["cargo", "check", "-p", "athena-selinger-linear-algebra"], "cargo check")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
