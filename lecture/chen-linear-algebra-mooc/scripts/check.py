#!/usr/bin/env python3
"""西电慕课《实用大众线性代数（MATLAB版）》视频课精读的验证入口：
内容结构（周→节）、课节元数据与课件段落锚点、题目出处硬门禁（verbatim/adapted + 课件页码或程序集号）、
用真 Octave 复算答案、底本（upstream/ 课件与程序集）完整性、公式自检与前端构建、cargo check。

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

# 出处档位 open（ADR 0089），但题源是本应用级硬门禁（ADR 0180 决策 5，沿 ADR 0177 决策 2）：
# 题目只许 verbatim / adapted；authored 不入库——使用者要求「出题必须有所本，不要凭空制造」。
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
    print(f"课表 {len(scope['chapters'])} 章 {len(ids)} 页")
    return {pid: load(CONTENT / "sections" / f"{pid}.json") for pid in ids if (CONTENT / "sections" / f"{pid}.json").is_file()}


# 把「难」归因于读者的措辞（主仓库 ADR 0013）：导学与解答都不许用这类词把难度推给读者
WRITING_BAN = ["显然", "容易看出", "不难证明", "只需注意到", "简单的计算", "众所周知", "读者自证", "易知", "不难发现"]


def texts_in_blocks(blocks):
    for b in blocks:
        t = b.get("t")
        if isinstance(t, str):
            yield t
        for key in ("q", "a"):
            if isinstance(b.get(key), str):
                yield b[key]
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


# 课件页码：p.12 或 p.12-15（连字符或波浪线）
SLIDE_PAGE = re.compile(r"p\.\d+([-–~]\d+)?")
SECTION_ID = re.compile(r"w\d{1,2}s\d{1,2}")


def walk_blocks(blocks):
    """所有块（含嵌套）。"""
    for b in blocks:
        yield b
        if "blocks" in b:
            yield from walk_blocks(b["blocks"])
        if b.get("k") == "list":
            for it in b["items"]:
                yield from walk_blocks(it)
        if b.get("k") == "dl":
            for it in b["items"]:
                yield from walk_blocks(it["blocks"])


def check_sections(sections: dict) -> None:
    total = 0
    seen_lessons: dict[tuple[int, int], str] = {}
    for pid, data in sections.items():
        if not data:
            continue
        total += 1
        if not SECTION_ID.fullmatch(pid):
            fail(f"{pid}: 节 id 必须形如 w1s1（第 1 周第 1 节）")
        joined = "\n".join(texts_in_blocks(data.get("blocks", [])))
        for w in WRITING_BAN:
            if w in joined:
                fail(f"{pid}: 导学含禁用词「{w}」")
        # 课节元数据（ADR 0180）：周/节号、课程大纲原题必填，且与节 id 一致、全局不重复
        lesson = data.get("lesson")
        if not isinstance(lesson, dict):
            fail(f"{pid}: 缺 lesson（周/节号与课程大纲原题）")
        else:
            wk, no = lesson.get("week"), lesson.get("no")
            if not (isinstance(wk, int) and isinstance(no, int)):
                fail(f"{pid}: lesson.week/no 必须是整数")
            else:
                if pid != f"w{wk}s{no}":
                    fail(f"{pid}: 节 id 与 lesson 的第 {wk} 周第 {no} 节不一致")
                if (wk, no) in seen_lessons:
                    fail(f"{pid}: 与 {seen_lessons[(wk, no)]} 的周/节号重复")
                seen_lessons[(wk, no)] = pid
            if not str(lesson.get("outline_title", "")).strip():
                fail(f"{pid}: lesson.outline_title 不能为空（逐字取自课程页大纲）")
            url = lesson.get("video_url")
            if url is not None and not str(url).startswith("https://"):
                fail(f"{pid}: lesson.video_url 只许 https 外链")
        # 课件段落必须有锚点：deck + 页码；看前提示/自答必须有正文
        n_slide = 0
        for b in walk_blocks(data.get("blocks", [])):
            k = b.get("k")
            if k == "slide":
                n_slide += 1
                if not str(b.get("deck", "")).strip() or not SLIDE_PAGE.fullmatch(str(b.get("page", ""))):
                    fail(f"{pid}: slide 需要 deck 与形如 p.12 / p.12-15 的 page，现在是 {b.get('deck')!r} {b.get('page')!r}")
                s_, e_ = b.get("start"), b.get("end")
                if s_ is not None and (not isinstance(s_, (int, float)) or (e_ is not None and e_ < s_)):
                    fail(f"{pid}: slide 的 start/end 必须是秒数且 end ≥ start")
            elif k == "prewatch" and not str(b.get("t", "")).strip():
                fail(f"{pid}: prewatch 不能为空")
            elif k == "recall" and (not str(b.get("q", "")).strip() or not str(b.get("a", "")).strip()):
                fail(f"{pid}: recall 需要 q 与 a")
        if n_slide == 0:
            fail(f"{pid}: 没有任何 slide 块（课件段落是本应用的文本底本，ADR 0180）")
    print(f"课节 {total} 节")


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


OCTAVE = shutil.which("octave-cli") or shutil.which("octave")


def octave_available() -> bool:
    return OCTAVE is not None


def octave_numbers(code: str) -> list[float]:
    """跑一段 Octave 代码，把变量 result（数或数组，按列展开）逐个打印出来并读回。"""
    prog = "format long; " + code + "\nprintf('@@RESULT@@\\n'); printf('%.17g\\n', double(result(:)));"
    r = subprocess.run([OCTAVE, "--no-gui", "--no-window-system", "--norc", "--quiet", "--eval", prog],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "octave 失败")
    tail = r.stdout.split("@@RESULT@@", 1)[1]
    return [float(x) for x in tail.split()]


def verify_answer(ex: dict, where: str) -> None:
    """用真 Octave 复算 numbers 题的答案：ex["verify"] 是一段 Octave 代码，须把结果赋给 result。"""
    code = ex.get("verify")
    if not code:
        return
    try:
        got = octave_numbers(code)
    except Exception as e:  # noqa: BLE001
        fail(f"{where}: verify 执行失败：{e}")
        return
    want = [float(a) for a in ex["check"]["answer"]]
    if len(got) != len(want) or any(abs(a - b) > 1e-6 * max(1, abs(b)) for a, b in zip(got, want)):
        fail(f"{where}: Octave 复算得 {got}，与 answer {want} 不符")


# 题 id：习题 1.3 → ex1-3，例题 1.4 → exl1-4（点号留给 节.题 分隔）
EX_ID = re.compile(r"exl?\d+-\d+[a-z]?$")
# locator 必须落在课件页码或程序集例题号上，如「课件 第1章 p.12」「课件 第1章 p.12 例 1.4」「程序集 pla106」
LOCATOR_SLIDE = re.compile(r"课件.*p\.\d+")
LOCATOR_PROGRAM = re.compile(r"pla\d{3}[a-z]?")


def check_exercises(sections: dict) -> None:
    n = verified = 0
    d = CONTENT / "exercises"
    if not d.is_dir():
        return
    can_verify = octave_available()
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
                fail(f"{where}: id 必须形如 ex1-3（习题）或 exl1-4（例题）")
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
                fail(f"{where}: 缺 source_refs（出题必须有所本，ADR 0180/0177）")
            for r in refs:
                rel = r.get("relation")
                if rel not in ALLOWED_RELATIONS:
                    fail(f"{where}: relation 必须是 verbatim/adapted，不能是 {rel!r}（authored 不入库）")
                    continue
                loc = str(r.get("locator", ""))
                if not LOCATOR_SLIDE.search(loc) and not LOCATOR_PROGRAM.search(loc):
                    fail(f"{where}: locator 要给到课件页码或程序集号，如「课件 第1章 p.12」「程序集 pla106」，现在是 {loc!r}")
                for prog in LOCATOR_PROGRAM.findall(loc):
                    if not (ROOT / "upstream" / "programs" / f"{prog}.m").is_file():
                        fail(f"{where}: locator 里的程序 {prog} 不在 upstream/programs/")
                if rel == "adapted" and not str(r.get("note", "")).strip():
                    fail(f"{where}: adapted 题必须在 note 写明对原书题的改动")

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
                    fail(f"{where}: numbers 题需要 verify（Octave 复算）或 verify_note（说明为何不能复算）")
            elif c.get("kind") == "choice":
                opts = c.get("options", [])
                if len(opts) < 2 or sum(1 for o in opts if o.get("ok")) != 1 or any(not o.get("why") or not o.get("text") for o in opts):
                    fail(f"{where}: choice 需要 ≥2 个选项、恰好 1 个 ok，且每项都有 text 与 why")
            else:
                fail(f"{where}: 未知 kind {c.get('kind')!r}")
    note = "" if can_verify else "；没装 octave，跳过复算"
    print(f"练习 {n} 道，Octave 复算 {verified} 道{note}")


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
            run(["cargo", "check", "-p", "athena-chen-linear-algebra-mooc"], "cargo check")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
