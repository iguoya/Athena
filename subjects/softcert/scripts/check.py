#!/usr/bin/env python3
"""软考应用的验证入口:内容结构校验、前端构建、Rust 侧检查与测试。

在仓库统一入口(python3 scripts/check.py)下与本应用单独跑都要能工作;
跨应用的出处检查由根 scripts/check-app-sources.mjs 按 content-contract.json
接管,这里不重复,只查本应用内容结构的自洽性。

内容结构是两层:章(chapter)= 官方教材的章,节(section)= 菜单里的
可学习单元。空章(sections 为空)是「待建」占位,合法;节一旦评级,
就必须有教学内容和考核题(TEACHING:评级只给已写出内容的章节)。

用法:
    python3 scripts/check.py [--skip-rust] [--content-only]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GRADE_VALUES = {"S", "A", "B", "C"}
MASTERY_GOALS = {"proficient", "understand", "aware"}
KNOWLEDGE_TYPES = {"concept", "skill", "strategy"}
BLOCK_TYPES = {"lead", "text", "formula", "compare", "steps", "table", "code", "callout", "viz"}
RELATIONS = {"authored", "verbatim", "quoted", "adapted"}


def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8,打印中文会抛 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str, hint: str = "") -> str:
    """Windows 上 npm 实际是 npm.cmd,which 按 PATHEXT 查出可执行路径(ADR 0047)。"""
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name},请先安装后重试。{hint}")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def fail(msg: str) -> None:
    raise SystemExit(f"内容校验失败:{msg}")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"{path.relative_to(PROJECT_ROOT)} 不是合法 JSON:{error}")


def check_content() -> None:
    """内容结构自洽:课程注册、教材章树、节评级、题目与出处、孤儿文件对账。"""
    print("== 内容结构校验 ==", flush=True)
    content = PROJECT_ROOT / "content"

    registry = load_json(content / "courses.json")
    courses = registry.get("courses", [])
    if not courses:
        fail("courses.json 没有注册任何课程")

    all_kp_ids: set[str] = set()
    section_ids: set[str] = set()  # 全部节 id(含未评级)
    referenced_sections: dict[str, set[str]] = {}  # 课程 id -> course.json 引用的节 id
    course_dirs: set[str] = set()

    for entry in courses:
        cid = entry.get("id")
        if not cid:
            fail(f"课程注册缺少 id:{entry}")
        course_path = content / cid / "course.json"
        if not course_path.is_file():
            fail(f"课程 {cid} 缺 course.json")
        course_dirs.add(cid)
        course = load_json(course_path)
        if course.get("id") != cid:
            fail(f"{cid}/course.json 的 id 与注册名不一致")
        tb = course.get("textbook", {})
        if not tb.get("id") or not tb.get("title"):
            fail(f"课程 {cid} 缺教材信息(textbook)")

        chapters = course.get("chapters", [])
        if not chapters:
            fail(f"课程 {cid} 没有章")
        last_no = 0
        refs = set()
        for ch in chapters:
            ch_id = ch.get("id", "")
            no = ch.get("no")
            if not isinstance(no, int) or no != last_no + 1:
                fail(f"{cid} 章 {ch_id} 的 no 必须从 1 连续递增(当前 {no},期望 {last_no + 1})")
            last_no = no
            if not ch.get("title"):
                fail(f"章 {ch_id} 缺标题")
            tb_ref = ch.get("textbook_ref", {})
            if tb_ref.get("sourceId") != tb.get("id") or not tb_ref.get("locator"):
                fail(f"章 {ch_id} 的 textbook_ref 必须指向本课程教材并带 locator")

            for sec in ch.get("sections", []):
                sid = sec.get("id", "")
                if sid in section_ids:
                    fail(f"节 id 重复:{sid}")
                section_ids.add(sid)
                refs.add(sid)
                if sec.get("grade") not in GRADE_VALUES:
                    fail(f"节 {sid} 的 grade 非法:{sec.get('grade')}")
                if sec.get("weight") not in (1, 2, 3):
                    fail(f"节 {sid} 的 weight 必须是 1–3")
                kp = sec.get("kp")
                if kp is None:
                    # 有内容但还没评级的过渡态允许;但必须有 lesson 文件才说得过去。
                    if not (content / cid / "chapters" / f"{sid}.json").is_file():
                        fail(f"节 {sid} 未评级且无教学内容:要么补评级,要么删掉条目")
                    continue
                all_kp_ids.add(kp.get("id", ""))
                if kp.get("difficulty") not in (1, 2, 3, 4, 5):
                    fail(f"节 {sid} 难度必须是 1–5")
                if kp.get("mastery_goal") not in MASTERY_GOALS:
                    fail(f"节 {sid} 掌握目标非法:{kp.get('mastery_goal')}")
                if kp.get("knowledge_type") not in KNOWLEDGE_TYPES:
                    fail(f"节 {sid} 知识类型非法:{kp.get('knowledge_type')}")
                # 评级只给已写出教学内容的章节:有评级就必须有内容,内容必须有题。
                if not (content / cid / "chapters" / f"{sid}.json").is_file():
                    fail(f"节 {sid} 有评级但没有教学内容文件")
                if not (content / cid / "quizzes" / f"{sid}.json").is_file():
                    fail(f"节 {sid} 有评级但没有考核题文件")
        referenced_sections[cid] = refs

    # requires 引用必须存在,防止先修链悬空(ADR 0030)。
    for cid in course_dirs:
        course = load_json(content / cid / "course.json")
        for ch in course.get("chapters", []):
            for sec in ch.get("sections", []):
                kp = sec.get("kp") or {}
                for req in kp.get("requires", []):
                    if req not in all_kp_ids:
                        fail(f"节 {sec['id']} 的 requires 引用了不存在的知识点:{req}")

    # viz 组件引用必须在注册表里(解析 src/viz/index.tsx 的 key 列表)。
    viz_index = (PROJECT_ROOT / "src" / "viz" / "index.tsx").read_text(encoding="utf-8")
    registered = set(re.findall(r'"([a-z0-9-]+)":\s', viz_index))
    question_count = 0
    lesson_files: set[str] = set()
    for course_file in sorted(content.glob("*/chapters/*.json")):
        lesson = load_json(course_file)
        rel = course_file.relative_to(PROJECT_ROOT)
        lesson_files.add(course_file.stem)
        blocks = lesson.get("blocks", [])
        if not blocks:
            fail(f"{rel} 没有任何内容块")
        for i, block in enumerate(blocks):
            btype = block.get("type")
            if btype not in BLOCK_TYPES:
                fail(f"{rel} 第 {i} 块类型非法:{btype}")
            if btype == "viz":
                comp = block.get("component", "")
                if comp not in registered:
                    fail(f"{rel} 第 {i} 块引用了未注册的可视化组件:{comp}")

    for quiz_file in sorted(content.glob("*/quizzes/*.json")):
        quiz = load_json(quiz_file)
        rel = quiz_file.relative_to(PROJECT_ROOT)
        questions = quiz.get("questions", [])
        if not questions:
            fail(f"{rel} 没有题目")
        for q in questions:
            question_count += 1
            options = q.get("options", [])
            if len(options) != 4:
                fail(f"{rel} 题目 {q.get('id')} 的选项不是 4 个")
            if not 0 <= q.get("answer", -1) < 4:
                fail(f"{rel} 题目 {q.get('id')} 的 answer 下标非法")
            if not q.get("explanation", "").strip():
                fail(f"{rel} 题目 {q.get('id')} 缺解析")
            src = q.get("source")
            if not isinstance(src, dict) or src.get("relation") not in RELATIONS:
                fail(f"{rel} 题目 {q.get('id')} 缺合法的 source(relation 字段)")
            if src.get("relation") == "authored" and not src.get("why"):
                fail(f"{rel} 题目 {q.get('id')} 是 authored 却没写为什么没有现成材料")

    # 孤儿文件对账:chapters/ 里的每个文件都必须被 course.json 引用——
    # 改名/迁移后残留的旧文件就是文档与内容漂移的起点。
    for cid in course_dirs:
        orphans = {p.stem for p in (content / cid / "chapters").glob("*.json")} - referenced_sections[cid]
        for orphan in sorted(orphans):
            fail(f"{cid}/chapters/{orphan}.json 没有被 course.json 引用(孤儿文件,删除或挂回)")

    papers = load_json(content / "past-exams" / "papers.json").get("papers", [])
    print(
        f"{len(course_dirs)} 门课、{len(section_ids)} 节、{question_count} 题、"
        f"{len(papers)} 份真题卷,结构自洽",
        flush=True,
    )


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    npm = tool("npm")
    if (PROJECT_ROOT / "package-lock.json").is_file():
        run([npm, "ci"], "安装前端依赖(按 lock)")
    else:
        run([npm, "install"], "安装前端依赖")


def main() -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="验证软考应用")
    parser.add_argument("--skip-rust", action="store_true", help="跳过 Rust 侧检查")
    parser.add_argument("--content-only", action="store_true", help="只跑内容校验")
    arguments = parser.parse_args()

    check_content()
    if arguments.content_only:
        return 0

    ensure_dependencies()
    # npm run build = tsc + vite build,类型和打包一次过。
    run([tool("npm"), "run", "build"], "前端类型检查与构建")

    if not arguments.skip_rust:
        # 不设 CARGO_TARGET_DIR:尊重外部环境;单独跑时用应用自己的 src-tauri/target。
        cargo = tool("cargo")
        run(
            [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            "Rust 侧检查",
        )
        run([cargo, "test", "--manifest-path", "src-tauri/Cargo.toml"], "Rust 侧测试")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
