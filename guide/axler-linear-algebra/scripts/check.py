#!/usr/bin/env python3
"""《线性代数应该这样学（第四版）》精读的验证入口：
内容结构、章导学文字、题目出处硬门禁（verbatim/adapted + 原书页码与题号）、
底本（upstream/ 官方中文版 PDF）完整性、公式自检与前端构建、cargo check。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash（主仓库 ADR 0047）。

用法：
    python3 scripts/check.py               # 全部检查
    python3 scripts/check.py --skip-rust   # 跳过 cargo check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ERRORS: list[str] = []

# 出处档位 open（ADR 0089），但题源是本应用级硬门禁（ADR 0179 决策 2）：
# 题目只许 verbatim / adapted；authored 不入库——题面必须有所本，不凭空制造。
ALLOWED_RELATIONS = ("verbatim", "adapted")


def fail(msg: str) -> None:
    ERRORS.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"{path.relative_to(ROOT)}: {e}")
        return None


def check_structure() -> dict:
    """scope.json（手写范围）↔ curriculum.json（手写课表）↔ sections/ 一致。"""
    scope = load(CONTENT / "scope.json")
    cur = load(CONTENT / "curriculum.json")
    if not scope or not cur:
        return {}
    ids = set()
    for ch in scope["chapters"]:
        for it in ch["items"]:
            if it["id"] in ids:
                fail(f"scope.json: 章 {it['id']} 重复")
            ids.add(it["id"])
            if not (CONTENT / "sections" / f"{it['id']}.json").is_file():
                fail(f"缺少章导学 content/sections/{it['id']}.json")
    extra = {p.stem for p in (CONTENT / "sections").glob("*.json")} - ids
    for e in sorted(extra):
        fail(f"sections/{e}.json 不在 scope.json 里（被裁掉的章不留文件）")
    cur_ids = {it["id"] for ch in cur["chapters"] for it in ch["items"] if it["page"]}
    if cur_ids != ids:
        fail("curriculum.json 与 scope.json 不一致（两者都手写，同步改）")
    print(f"课表 {len(scope['chapters'])} 组 {len(ids)} 页")
    return {pid: load(CONTENT / "sections" / f"{pid}.json") for pid in ids if (CONTENT / "sections" / f"{pid}.json").is_file()}


# 把「难」归因于读者的措辞（主仓库 ADR 0013）：导学与解答都不许用这类词把难度推给读者
WRITING_BAN = ["显然", "容易看出", "不难证明", "只需注意到", "简单的计算", "众所周知", "读者自证", "易知", "不难发现"]


def texts_in_blocks(blocks):
    for b in blocks:
        t = b.get("t")
        if isinstance(t, str):
            yield t
        if isinstance(b.get("title"), str):
            yield b["title"]
        if "blocks" in b:
            yield from texts_in_blocks(b["blocks"])
        if b.get("k") == "list":
            for it in b["items"]:
                yield from texts_in_blocks(it)
        if b.get("k") == "dl":
            for it in b["items"]:
                yield it["term"]
                yield from texts_in_blocks(it["blocks"])


def check_sections(sections: dict) -> None:
    total = 0
    for pid, data in sections.items():
        if not data:
            continue
        total += 1
        joined = "\n".join(texts_in_blocks(data.get("blocks", [])))
        for w in WRITING_BAN:
            if w in joined:
                fail(f"{pid}: 导学含禁用词「{w}」")
    print(f"章导学 {total} 章")


def check_figures(sections: dict) -> None:
    """讲解里的每个 figure 块都要有 content/figures/<id>.svg（手工或脚本自备，进 git）。"""
    need = set()

    def walk(bl):
        for b in bl:
            if b.get("k") == "figure":
                need.add(b["id"])
            if "blocks" in b:
                walk(b["blocks"])
            if b.get("k") == "list":
                for it in b["items"]:
                    walk(it)
            if b.get("k") == "dl":
                for it in b["items"]:
                    walk(it["blocks"])

    for data in sections.values():
        if data:
            walk(data["blocks"])
    for fid in sorted(need):
        if not (CONTENT / "figures" / f"{fid}.svg").is_file():
            fail(f"缺图 content/figures/{fid}.svg")
    print(f"插图 {len(need)} 幅")


# 题 id 用原书编号：习题 1A 9 → ex1a-9，第 4 章习题（无节字母）3 → ex4-3；
# 字母一律小写（点号留给 chapter.item 分隔）
EX_ID = re.compile(r"ex\d[a-f]?-\d+[a-z]?$")
# locator 必须给到原书印刷页码与题号，如「p.23 习题 1A 9」「p.123 习题 4 3」。
# 页码以 PDF 页眉的原书印刷页码为准（PDF 0-based 页号 − 13 = 印刷页码，见 AGENTS.md）。
LOCATOR_PAGE = re.compile(r"(p\.?\s*\d+|\d+\s*页)")
LOCATOR_NUM = re.compile(r"习题\s*\d+[A-F]?\s*\d+")


def check_exercises(sections: dict) -> None:
    n = 0
    d = CONTENT / "exercises"
    if not d.is_dir():
        return
    for p in sorted(d.glob("*.json")):
        data = load(p)
        if data is None:
            continue
        if p.stem not in sections:
            fail(f"exercises/{p.name}: 没有对应的章")
            continue
        seen = set()
        for ex in data:
            n += 1
            eid = ex.get("id", "?")
            where = f"exercises/{p.name}:{eid}"
            if not EX_ID.fullmatch(str(eid)):
                fail(f"{where}: id 必须形如 ex1a-9（习题 1A 9）或 ex4-3（习题 4 3），字母小写")
            if eid in seen:
                fail(f"{where}: id 重复")
            seen.add(eid)
            if not str(ex.get("stem", "")).strip() or not str(ex.get("sol", "")).strip():
                fail(f"{where}: stem 与 sol 都不能为空")
            for w in WRITING_BAN:
                if w in ex.get("stem", "") + ex.get("sol", ""):
                    fail(f"{where}: 含禁用词「{w}」")

            # 出处硬门禁：每道题必须有 source_refs；只收 verbatim / adapted；locator 到页码与题号
            refs = ex.get("source_refs") or []
            if not refs:
                fail(f"{where}: 缺 source_refs（出题必须有所本，ADR 0179）")
            for r in refs:
                rel = r.get("relation")
                if rel not in ALLOWED_RELATIONS:
                    fail(f"{where}: relation 必须是 verbatim/adapted，不能是 {rel!r}（authored 不入库）")
                    continue
                loc = str(r.get("locator", ""))
                if not LOCATOR_PAGE.search(loc) or not LOCATOR_NUM.search(loc):
                    fail(f"{where}: locator 要给到原书页码与题号，如「p.23 习题 1A 9」，现在是 {loc!r}")
                if rel == "adapted" and not str(r.get("note", "")).strip():
                    fail(f"{where}: adapted 题必须在 note 写明对原书题的改动")
                if rel == "verbatim" and "自设" not in str(r.get("note", "")):
                    # 判分选项是应用自设的教学层，必须声明，不冒充原书内容（ADR 0179 决策 4）
                    fail(f"{where}: verbatim 题的 note 需声明「判分选项为应用自设」")

            c = ex.get("check", {})
            if c.get("kind") == "choice":
                opts = c.get("options", [])
                if len(opts) < 2 or sum(1 for o in opts if o.get("ok")) != 1 or any(not o.get("why") or not o.get("text") for o in opts):
                    fail(f"{where}: choice 需要 ≥2 个选项、恰好 1 个 ok，且每项都有 text 与 why")
            else:
                fail(f"{where}: 未知 kind {c.get('kind')!r}（本应用只收 choice：证明对错无法机判，ADR 0179 决策 4）")
    print(f"原书习题 {n} 道")


def check_upstream() -> None:
    """底本完整性：upstream.json 记录的每个文件都要在，且 SHA-256 一致。"""
    up = load(ROOT / "upstream.json")
    if not up:
        fail("缺少 upstream.json（书目信息与文件校验和）")
        return
    for name, digest in up.get("sha256", {}).items():
        p = ROOT / "upstream" / name
        if not p.is_file():
            fail(f"upstream/{name}: 底本文件缺失")
            continue
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != digest:
            fail(f"upstream/{name}: SHA-256 与 upstream.json 不符")
    print(f"底本 {len(up.get('sha256', {}))} 件核对完成")


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
    check_sections(sections)
    check_figures(sections)
    check_exercises(sections)
    check_upstream()
    for need in ("docs/COVERAGE.md", "docs/LICENSE-NOTICE.md"):
        if not (ROOT / need).is_file():
            fail(f"缺少 {need}")
    if not ERRORS:
        if not (ROOT / "node_modules").is_dir():
            run(["pnpm", "install"], "安装前端依赖")
        run(["pnpm", "run", "build"], "公式自检 + 前端构建")
        if not args.skip_rust:
            run(["cargo", "check", "-p", "athena-axler-linear-algebra"], "cargo check")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
