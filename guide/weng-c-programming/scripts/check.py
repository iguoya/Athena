#!/usr/bin/env python3
"""翁恺《C语言程序设计》视频课的验证入口：
课表 ↔ 课堂脚本一致、节拍与任务的结构与数量门槛、判分题的出处硬门禁（locator 必须是视频里真有的时间）、
「你来做」骨架用本机 C 编译器编译运行并比对输出、公式自检与前端构建、cargo check。

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
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ERRORS: list[str] = []

# 出处档位 open（ADR 0089），但判分题的题源是本应用级硬门禁（ADR 0182 决策 7）：
# 只许 verbatim / adapted，authored 不入库；locator 是「P<分集号> <mm:ss>」，时间必须落在转写里讲师讲到该内容的位置附近。
ALLOWED_RELATIONS = ("verbatim", "adapted")
LOCATOR = re.compile(r"P(\d+) (\d{1,2}):(\d{2})")
LOCATOR_SLACK = 6.0  # 转写时间戳与讲师实际说话位置的容差（秒）

# 任务数量门槛（zcode 评审、DESIGN-v2 第 3 节）：一节总任务 ≤10、重任务（你来做）≤2、每节拍暂停任务 ≤2
MAX_TASKS, MAX_HEAVY, MAX_PAUSE_PER_BEAT = 10, 2, 2
JUDGED = ("quick", "doit")  # 进掌握度的任务类型
TASK_KINDS = ("predict", "selfexplain", "quick", "doit")

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
            if k != "transcript":  # 转写是机器文本，不查措辞
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


def check_check(c: dict, where: str) -> None:
    kind = c.get("kind")
    if kind == "numbers":
        if not c.get("answer") or not all(isinstance(x, (int, float)) for x in c["answer"]):
            fail(f"{where}: numbers 的 answer 必须是非空数字数组")
        if not str(c.get("ask", "")).strip():
            fail(f"{where}: numbers 需要 ask（告诉学习者答案写成什么形式）")
    elif kind == "choice":
        opts = c.get("options", [])
        if len(opts) < 2 or sum(1 for o in opts if o.get("ok")) != 1 or any(not o.get("why") or not o.get("text") for o in opts):
            fail(f"{where}: choice 需要 ≥2 个选项、恰好 1 个 ok，且每项都有 text 与 why")
    elif kind == "output":
        if not str(c.get("expected", "")).strip() or not str(c.get("ask", "")).strip():
            fail(f"{where}: output 需要 ask 与 expected")
    else:
        fail(f"{where}: 未知 check.kind {kind!r}")


def transcript_covers(lesson: dict, t: float) -> bool:
    segs = (lesson.get("transcript") or {}).get("segments") or []
    return any(s["start"] - LOCATOR_SLACK <= t <= s["end"] + LOCATOR_SLACK for s in segs)


def check_source_refs(task: dict, lesson: dict, where: str) -> None:
    refs = task.get("source_refs") or []
    if not refs:
        fail(f"{where}: 进掌握度的题缺 source_refs（出题必须有所本，ADR 0182）")
    for r in refs:
        if r.get("relation") not in ALLOWED_RELATIONS:
            fail(f"{where}: relation 必须是 verbatim/adapted，不能是 {r.get('relation')!r}（authored 不入库）")
            continue
        m = LOCATOR.fullmatch(str(r.get("locator", "")))
        if not m:
            fail(f"{where}: locator 要写成「P3 05:12」（分集号 + 视频里的时间），现在是 {r.get('locator')!r}")
            continue
        p, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
        t = mm * 60 + ss
        if p != lesson["video"]["p"]:
            fail(f"{where}: locator 的分集号 P{p} 与本课 P{lesson['video']['p']} 不一致")
        if t > lesson["video"]["duration"] + 1:
            fail(f"{where}: locator 时间 {mm}:{ss:02d} 超出视频时长")
        elif lesson.get("transcript") and not transcript_covers(lesson, t):
            fail(f"{where}: locator 时间 {mm}:{ss:02d} 在转写里找不到对应的讲课内容（不得凭印象写时间）")
        if r["relation"] == "adapted" and not str(r.get("note", "")).strip():
            fail(f"{where}: adapted 题必须在 note 写明对原内容的改动")


GCC = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")


def run_c(code: str) -> str | None:
    """用本机 C 编译器编译运行骨架代码，返回标准输出；编译或运行失败返回 None。"""
    with tempfile.TemporaryDirectory() as d:
        src, exe = Path(d) / "t.c", Path(d) / ("t.exe" if sys.platform == "win32" else "t")
        src.write_text(code, encoding="utf-8")
        if subprocess.run([GCC, str(src), "-o", str(exe)], capture_output=True).returncode != 0:
            return None
        r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10, cwd=d)
        return r.stdout if r.returncode == 0 else None


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
            for s in strings_in({k: lesson[k] for k in ("title", "opening", "beats", "closing")}):
                for w in WRITING_BAN:
                    if w in s:
                        fail(f"{where0}: 含禁用词「{w}」")
            tr = lesson.get("transcript")
            if tr and "机器转写" not in str(tr.get("status", "")):
                fail(f"{where0}: transcript.status 必须标明「机器转写」及校对状态（ADR 0182 决策 8）")

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
                    if not 0 <= s < e <= v["duration"] + 1:
                        fail(f"{bw}: 节拍起止 {s}–{e} 不合法或超出视频时长")
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
                if kind == "doit":
                    heavy += 1
                if kind == "predict":
                    check_check(t.get("check", {}), tw)
                    if t["check"].get("kind") == "output":
                        fail(f"{tw}: 预测题只许选择/数值（机器可判），不许贴输出")
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
                    if kind == "doit":
                        sk = str(t.get("skeleton", ""))
                        if not sk.strip():
                            fail(f"{tw}: doit 需要骨架代码（不改也能编译运行，ADR 0059）")
                        elif t["check"].get("kind") != "output":
                            fail(f"{tw}: doit 的 check 必须是 output")
                        elif GCC:
                            out = run_c(sk)
                            if out is None:
                                fail(f"{tw}: 骨架代码编译或运行失败")
                            elif out.replace("\r\n", "\n").strip() != str(t["check"]["expected"]).replace("\r\n", "\n").strip():
                                fail(f"{tw}: 骨架运行输出与 expected 不符：{out.strip()!r}")
            if len(tasks) > MAX_TASKS:
                fail(f"{where0}: 一节任务 {len(tasks)} 个，超过上限 {MAX_TASKS}（该拆节或并任务）")
            if heavy > MAX_HEAVY:
                fail(f"{where0}: 重任务（你来做）{heavy} 个，超过上限 {MAX_HEAVY}")
            n_tasks_all += len(tasks)
    judged = sum(1 for l in lessons.values() if l for b in l["beats"] for t in b["tasks"] if t.get("kind") in JUDGED)
    print(f"课堂脚本 {len(lessons)} 节，任务 {n_tasks_all} 个（其中节拍内判分题 {judged} 道）")
    if not GCC:
        print("没找到 C 编译器，跳过「你来做」骨架的编译运行核对")


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
            run(["cargo", "check", "-p", "athena-weng-c-programming"], "cargo check")
            run(["cargo", "test", "-p", "athena-weng-c-programming", "--lib"], "cargo test")
    if ERRORS:
        print("\n不通过：", file=sys.stderr)
        for e in ERRORS:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print("\n通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
