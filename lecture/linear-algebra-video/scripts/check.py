#!/usr/bin/env python3
"""线性代数（工）·视频课的验证入口：
课表 ↔ 课堂脚本一致、节拍与任务的结构与数量门槛、判分题的出处硬门禁（locator 必须是视频里真有的时间）、
数值题用 sympy 复算（`verify`）、公式自检与前端构建、cargo check。

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
CRATE = "athena-linear-algebra-video"
ERRORS: list[str] = []

# 判分题的题源是本应用级硬门禁（ADR 0185 决策 6，沿 ADR 0182 决策 7）：
# 只许 verbatim / adapted，authored 不入库；locator 是「P<分集号> <mm:ss>」，时间必须落在字幕里讲师讲到该内容的位置附近。
ALLOWED_RELATIONS = ("verbatim", "adapted")
LOCATOR = re.compile(r"P(\d+) (\d{1,2}):(\d{2})")
LOCATOR_SLACK = 6.0  # 字幕时间戳与讲师实际说话位置的容差（秒）

# 任务数量门槛（ADR 0185 决策 3，沿翁恺）：一节总任务 ≤10、重任务（先自己算）≤2、每节拍暂停任务 ≤2
MAX_TASKS, MAX_HEAVY, MAX_PAUSE_PER_BEAT = 10, 2, 2
JUDGED = ("quick", "workout")  # 进掌握度的任务类型
TASK_KINDS = ("predict", "selfexplain", "quick", "workout")

# 把「难」归因于读者的措辞（主仓库 ADR 0013）
WRITING_BAN = ["显然", "容易看出", "不难证明", "只需注意到", "简单的计算", "众所周知", "读者自证", "易知", "不难发现"]


def fail(msg: str) -> None:
    ERRORS.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"{path.relative_to(ROOT)}: {e}")
        return None


def strings_in(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for x in node:
            yield from strings_in(x)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k not in ("transcript", "verify"):  # 转写是机器文本，verify 是代码，都不查措辞
                yield from strings_in(v)


def check_structure() -> dict:
    """curriculum.json（课表）↔ lessons/ 一致。"""
    cur = load(CONTENT / "curriculum.json")
    if not cur:
        return {}
    ids: list[str] = []
    for ch in cur["chapters"]:
        for it in ch["items"]:
            if it["id"] in ids:
                fail(f"curriculum.json: 课节 {it['id']} 重复")
            ids.append(it["id"])
            if not (CONTENT / "lessons" / f"{it['id']}.json").is_file():
                fail(f"缺少课堂脚本 content/lessons/{it['id']}.json")
    extra = {p.stem for p in (CONTENT / "lessons").glob("*.json")} - set(ids)
    for e in sorted(extra):
        fail(f"lessons/{e}.json 不在 curriculum.json 里（没做进课表的脚本不留文件）")
    print(f"课表 {len(cur['chapters'])} 章 {len(ids)} 节")
    return {i: load(CONTENT / "lessons" / f"{i}.json") for i in ids if (CONTENT / "lessons" / f"{i}.json").is_file()}


def check_check(c: dict, where: str, require_why: bool = True) -> None:
    kind = c.get("kind")
    if kind == "numbers":
        if not c.get("answer") or not all(isinstance(x, (int, float)) for x in c["answer"]):
            fail(f"{where}: numbers 的 answer 必须是非空数字数组")
        if not str(c.get("ask", "")).strip():
            fail(f"{where}: numbers 需要 ask（告诉学习者答案写成什么形式）")
    elif kind == "choice":
        opts = c.get("options", [])
        # 预测题的 why 可以留空：作答后不逐项解释，由 reveal 统一讲（开场预测不剧透）
        if len(opts) < 2 or sum(1 for o in opts if o.get("ok")) != 1 or any(not o.get("text") or (require_why and not o.get("why")) for o in opts):
            fail(f"{where}: choice 需要 ≥2 个选项、恰好 1 个 ok，且每项都有 text{' 与 why' if require_why else ''}")
    else:
        fail(f"{where}: 未知 check.kind {kind!r}（只有 numbers、choice）")


def transcript_covers(lesson: dict, t: float) -> bool:
    segs = (lesson.get("transcript") or {}).get("segments") or []
    return any(s["start"] - LOCATOR_SLACK <= t <= s["end"] + LOCATOR_SLACK for s in segs)


def check_source_refs(task: dict, lesson: dict, where: str) -> None:
    refs = task.get("source_refs") or []
    if not refs:
        fail(f"{where}: 进掌握度的题缺 source_refs（出题必须有所本，ADR 0185 决策 6）")
    v = lesson["video"]
    lo, hi = v.get("start", 0), v.get("end", v["duration"])
    for r in refs:
        if r.get("relation") not in ALLOWED_RELATIONS:
            fail(f"{where}: relation 必须是 verbatim/adapted，不能是 {r.get('relation')!r}（authored 不入库）")
            continue
        m = LOCATOR.fullmatch(str(r.get("locator", "")))
        if not m:
            fail(f"{where}: locator 要写成「P6 05:12」（分集号 + 视频里的时间），现在是 {r.get('locator')!r}")
            continue
        p, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
        t = mm * 60 + ss
        if p != v["p"]:
            fail(f"{where}: locator 的分集号 P{p} 与本课 P{v['p']} 不一致")
        if t > v["duration"] + 1:
            fail(f"{where}: locator 时间 {mm}:{ss:02d} 超出视频时长")
        elif not lo - LOCATOR_SLACK <= t <= hi + LOCATOR_SLACK:
            fail(f"{where}: locator 时间 {mm}:{ss:02d} 不在本课课节区间 {lo}–{hi} 秒内")
        elif lesson.get("transcript") and not transcript_covers(lesson, t):
            fail(f"{where}: locator 时间 {mm}:{ss:02d} 在字幕里找不到对应的讲课内容（不得凭印象写时间）")
        if r["relation"] == "adapted" and not str(r.get("note", "")).strip():
            fail(f"{where}: adapted 题必须在 note 写明对原内容的改动")


try:
    import sympy  # noqa: F401
except ImportError:  # ADR 0057：假定开发机是完整的，缺工具时只给安装指引
    sympy = None


def run_verify(code: str, where: str):
    """执行 verify 代码（可用 sympy 全部名字），要求它把结果放进变量 result；失败返回 None。"""
    ns: dict = {}
    try:
        exec("from sympy import *\n" + code, ns)  # noqa: S102 —— 内容文件是本仓库自己的，不是外部输入
    except Exception as e:  # noqa: BLE001
        fail(f"{where}: verify 执行出错：{e!r}")
        return None
    if "result" not in ns:
        fail(f"{where}: verify 必须给变量 result 赋值")
        return None
    return ns["result"]


def check_verify(task: dict, where: str) -> None:
    """数值题必须带 verify，并与 answer 一致；选择题的 verify 可选，给出的是正确选项的下标。"""
    c = task["check"]
    code = task.get("verify")
    if c.get("kind") == "numbers" and not str(code or "").strip():
        fail(f"{where}: 数值题必须带 verify（用 sympy 复算答案，ADR 0185 决策 5）")
        return
    if not str(code or "").strip():
        return
    if sympy is None:
        print(f"没装 sympy，跳过 {where} 的 verify 复算（pip install sympy）")
        return
    got = run_verify(code, where)
    if got is None:
        return
    if c.get("kind") == "numbers":
        vals = list(got) if isinstance(got, (list, tuple)) else [got]
        try:
            nums = [float(sympy.N(v)) for v in vals]
        except Exception as e:  # noqa: BLE001
            fail(f"{where}: verify 的 result 不是数 {got!r}：{e!r}")
            return
        want = [float(x) for x in c["answer"]]
        if len(nums) != len(want) or any(abs(a - b) > 1e-6 * max(1, abs(b)) for a, b in zip(nums, want)):
            fail(f"{where}: verify 复算得 {nums}，与 answer {want} 不符")
    else:
        ok = [i for i, o in enumerate(c["options"]) if o.get("ok")]
        if got not in ok:
            fail(f"{where}: verify 说正确选项下标是 {got!r}，但标 ok 的是 {ok}")


def check_lessons(lessons: dict) -> None:
    n_tasks_all = 0
    for lid, lesson in lessons.items():
        if not lesson:
            continue
        where0 = f"lessons/{lid}.json"
        for key in ("id", "title", "video", "opening", "beats", "closing"):
            if key not in lesson:
                fail(f"{where0}: 缺字段 {key}")
                break
        else:
            if lesson["id"] != lid:
                fail(f"{where0}: id {lesson['id']!r} 与文件名不一致")
            v = lesson["video"]
            if v.get("kind") != "bilibili" or not re.fullmatch(r"BV[0-9A-Za-z]{10}", str(v.get("bvid", ""))) or not isinstance(v.get("p"), int) or v["p"] < 1:
                fail(f"{where0}: video 需要 kind=bilibili、合法 bvid 与分集号 p")
            if not isinstance(v.get("duration"), (int, float)) or v["duration"] <= 0:
                fail(f"{where0}: video.duration 必须是正数（秒）")
            if ("start" in v) != ("end" in v):
                fail(f"{where0}: video.start 与 video.end 要么都写要么都不写")
            lo, hi = v.get("start", 0), v.get("end", v["duration"])
            if not 0 <= lo < hi <= v["duration"] + 1:
                fail(f"{where0}: 课节区间 {lo}–{hi} 不合法或超出视频时长")
            for s in strings_in({k: lesson[k] for k in ("title", "opening", "beats", "closing")}):
                for w in WRITING_BAN:
                    if w in s:
                        fail(f"{where0}: 含禁用词「{w}」")
            tr = lesson.get("transcript")
            if tr and "校对" not in str(tr.get("status", "")):
                fail(f"{where0}: transcript.status 必须标明来源性质（平台字幕/机器转写）与校对状态（ADR 0185 决策 7）")

            beats = lesson["beats"]
            if not 3 <= len(beats) <= 6:
                fail(f"{where0}: 节拍数应在 3–6 之间，现在是 {len(beats)}")
            tasks: list[tuple[str, dict, dict | None]] = []
            if lesson["opening"].get("predict"):
                tasks.append(("opening", lesson["opening"]["predict"], None))
            seen_ids: set[str] = set()
            prev_end = None
            for b in beats:
                bw = f"{where0}:{b.get('id', '?')}"
                for key in ("id", "title", "concept", "tasks", "takeaway"):
                    if not b.get(key):
                        fail(f"{bw}: 节拍缺 {key}")
                s, e = b.get("start"), b.get("end")
                if (s is None) != (e is None):
                    fail(f"{bw}: start 与 end 要么都标要么都空")
                if s is not None and e is not None:
                    if not lo - 0.5 <= s < e <= hi + 0.5:
                        fail(f"{bw}: 节拍起止 {s}–{e} 不合法或超出课节区间 {lo}–{hi}")
                    if prev_end is not None and s < prev_end - 0.5:
                        fail(f"{bw}: 节拍与上一个重叠")
                    prev_end = e
                pause = [t for t in b.get("tasks", []) if t.get("at") is not None]
                if len(pause) > MAX_PAUSE_PER_BEAT:
                    fail(f"{bw}: 暂停点任务 {len(pause)} 个，超过上限 {MAX_PAUSE_PER_BEAT}（推导中途别连弹）")
                for t in b.get("tasks", []):
                    at = t.get("at")
                    if at is not None and s is not None and e is not None and not (s - 0.5 <= at <= e + 0.5):
                        fail(f"{bw}:{t.get('id')}: 暂停点 {at} 不在本节拍 {s}–{e} 内")
                    tasks.append((bw, t, b))
            for k in lesson["closing"].get("exit", []):
                tasks.append((f"{where0}:closing", k, None))
            if not str(lesson["closing"].get("note_prompt", "")).strip():
                fail(f"{where0}: closing.note_prompt 不能为空")

            heavy = 0
            for bw, t, _ in tasks:
                tw = f"{bw}:{t.get('id', '?')}"
                if t.get("id") in seen_ids:
                    fail(f"{tw}: 任务 id 重复")
                seen_ids.add(t.get("id"))
                kind = t.get("kind")
                if kind not in TASK_KINDS:
                    fail(f"{tw}: 未知任务类型 {kind!r}")
                    continue
                if kind == "workout":
                    heavy += 1
                if kind == "predict":
                    check_check(t.get("check", {}), tw, require_why=False)
                    if not str(t.get("reveal", "")).strip():
                        fail(f"{tw}: predict 需要 reveal")
                elif kind == "selfexplain":
                    if not str(t.get("prompt", "")).strip() or not str(t.get("reference", "")).strip():
                        fail(f"{tw}: selfexplain 需要 prompt 与 reference")
                else:
                    check_check(t.get("check", {}), tw)
                    if not str(t.get("stem", "")).strip() or not str(t.get("sol", "")).strip():
                        fail(f"{tw}: stem 与 sol 都不能为空")
                    check_source_refs(t, lesson, tw)
                    if t.get("check", {}).get("kind") in ("numbers", "choice"):
                        check_verify(t, tw)
            if len(tasks) > MAX_TASKS:
                fail(f"{where0}: 一节任务 {len(tasks)} 个，超过上限 {MAX_TASKS}（该拆节或并任务）")
            if heavy > MAX_HEAVY:
                fail(f"{where0}: 重任务（先自己算）{heavy} 个，超过上限 {MAX_HEAVY}")
            n_tasks_all += len(tasks)
    judged = sum(1 for l in lessons.values() if l for b in l["beats"] for t in b["tasks"] if t.get("kind") in JUDGED)
    print(f"课堂脚本 {len(lessons)} 节，任务 {n_tasks_all} 个（其中节拍内判分题 {judged} 道）")
    if sympy is None:
        print("没找到 sympy：数值题的 verify 复算被跳过（pip install sympy）")


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
    lessons = check_structure()
    check_lessons(lessons)
    for need in ("docs/LICENSE-NOTICE.md",):
        if not (ROOT / need).is_file():
            fail(f"缺少 {need}")
    if not ERRORS:
        if not (ROOT / "node_modules").is_dir():
            run(["pnpm", "install"], "安装前端依赖")
        run(["pnpm", "run", "build"], "公式自检 + 前端构建")
        if not args.skip_rust:
            run(["cargo", "check", "-p", CRATE], "cargo check")
            run(["cargo", "test", "-p", CRATE, "--lib"], "cargo test")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
