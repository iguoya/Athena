#!/usr/bin/env python3
"""SymPy 官方教程精读的验证入口：内容结构、译文与原文的公式和代码一致、试一试（含用真 SymPy 复算答案）、出处契约、构建。

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
    """与 src/splitInline.ts 的 splitInline 同一规则：收尾的 $ 必须在花括号深度 0。"""
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
    pages = [it["id"] for ch in scope["parts"] for it in ch["items"]]
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
    print(f"课表 {len(scope['parts'])} 部分 {len(pages)} 页")
    return {pid: load(CONTENT / "sections" / f"{pid}.json") for pid in pages if (CONTENT / "sections" / f"{pid}.json").is_file()}


# 把「难」归因于读者的措辞（主仓库 ADR 0013）：原书没有这类说法，译文也不许添
WRITING_BAN = ["显然", "容易看出", "不难证明", "只需注意到", "简单的计算", "众所周知", "读者自证", "易知", "不难发现"]


def code_spans(s: str) -> list[str]:
    return sorted(re.findall(r"`[^`]+`", s))


def check_translations(sections: dict) -> None:
    total = done = 0
    for pid, data in sections.items():
        if not data:
            continue
        for u in units(data["blocks"]):
            total += 1
            if not u.get("zh"):
                continue
            done += 1
            for w in WRITING_BAN:
                if w in u["zh"]:
                    fail(f"{pid}: 译文含禁用词「{w}」：{u['zh'][:60]}")
            # 译文只许改公式与代码外的文字：公式、行内代码集合必须与原文一致
            if sorted(inline_math(u["zh"])) != sorted(inline_math(u["en"])):
                fail(f"{pid}: 译文公式与原文不一致\n    en: {u['en'][:90]}\n    zh: {u['zh'][:90]}")
            if code_spans(u["zh"]) != code_spans(u["en"]):
                fail(f"{pid}: 译文里的行内代码与原文不一致\n    en: {u['en'][:90]}\n    zh: {u['zh'][:90]}")
    print(f"可译单元 {total}，已译 {done}（{done * 100 // max(total, 1)}%）")


def sympy_available() -> bool:
    try:
        import sympy  # noqa: F401
        return True
    except ImportError:
        return False


def verify_answer(ex: dict, where: str) -> None:
    """用真 SymPy 复算 numbers 题的答案：ex["verify"] 是一段 Python，须把结果（数或数的列表）赋给 result。"""
    code = ex.get("verify")
    if not code:
        return
    ns: dict = {}
    try:
        exec("from sympy import *\nx, y, z, t = symbols('x y z t')\n" + code, ns)  # noqa: S102 —— 本仓库手写内容，非外部输入
        got = ns["result"]
        got = [got] if not isinstance(got, (list, tuple)) else list(got)
        got = [float(ns["N"](g)) for g in got]
    except Exception as e:  # noqa: BLE001
        fail(f"{where}: verify 执行失败：{e}")
        return
    want = [float(a) for a in ex["check"]["answer"]]
    if len(got) != len(want) or any(abs(a - b) > 1e-6 * max(1, abs(b)) for a, b in zip(got, want)):
        fail(f"{where}: SymPy 复算得 {got}，与 answer {want} 不符")


def check_exercises(sections: dict) -> None:
    n = verified = 0
    d = CONTENT / "exercises"
    if not d.is_dir():
        return
    can_verify = sympy_available()
    for p in sorted(d.glob("*.json")):
        data = load(p)
        if data is None:
            continue
        if sections and p.stem not in sections and len(sections) < 5:
            continue  # lint_checks.py 只传了几节时，不检查别的文件
        if p.stem not in sections:
            fail(f"exercises/{p.name}: 没有对应的节")
            continue
        seen = set()
        for ex in data:
            n += 1
            eid = ex.get("id", "?")
            where = f"exercises/{p.name}:{eid}"
            if eid in seen or not re.fullmatch(r"ex\d+", str(eid)):
                fail(f"{where}: id 必须是 ex<数字> 且不重复")
            seen.add(eid)
            if not str(ex.get("stem", "")).strip() or not str(ex.get("sol", "")).strip():
                fail(f"{where}: stem 与 sol 都不能为空")
            for w in WRITING_BAN:
                if w in ex.get("stem", "") + ex.get("sol", ""):
                    fail(f"{where}: 含禁用词「{w}」")
            refs = ex.get("source_refs") or []
            if not refs or any(r.get("relation") != "authored" for r in refs):
                fail(f"{where}: source_refs 必须标 relation=authored")
            c = ex.get("check", {})
            if c.get("kind") == "numbers":
                if not c.get("answer") or not all(isinstance(x, (int, float)) for x in c["answer"]):
                    fail(f"{where}: numbers 的 answer 必须是非空数字数组")
                if not str(c.get("ask", "")).strip():
                    fail(f"{where}: numbers 需要 ask（告诉学习者答案写成什么形式）")
                if ex.get("verify"):
                    if can_verify:
                        verify_answer(ex, where)
                        verified += 1
                elif not ex.get("verify_note"):
                    fail(f"{where}: numbers 题需要 verify（SymPy 复算）或 verify_note（说明为何不能复算）")
            elif c.get("kind") == "choice":
                opts = c.get("options", [])
                if len(opts) < 2 or sum(1 for o in opts if o.get("ok")) != 1 or any(not o.get("why") or not o.get("text") for o in opts):
                    fail(f"{where}: choice 需要 ≥2 个选项、恰好 1 个 ok，且每项都有 text 与 why")
            else:
                fail(f"{where}: 未知 kind {c.get('kind')!r}")
    note = "" if can_verify else "；没装 sympy，跳过复算"
    print(f"试一试 {n} 道，SymPy 复算 {verified} 道{note}")


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
    check_exercises(sections)
    if (ROOT / "upstream" / "sympy").is_dir():
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
            run(["cargo", "check", "-p", "athena-sympy-tutorial"], "cargo check")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
