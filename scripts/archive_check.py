"""跨应用检查：各应用 `content/archive.json`（历史归档章节，ADR 0176）。

归档条目是从旧仓库原样搬来的代码加新写的批注。这里守的是“搬得对、批得准”的底线：
案例目录和源文件真实存在、批注的行号真的落在文件里、出处写全、知识点 id 不撞主课表、
先修指向存在的知识点，以及每个 `arc_*` 案例目录都被某个条目引用（不留孤儿）。
内容好不好（批注是否说到点上）机器查不了，由 leader 抽查。
"""
from __future__ import annotations

import json
from pathlib import Path

RUN_MODES = ("cli", "toolchain", "linux-only", "read-only")
NOTE_KINDS = ("naming", "ownership", "coupling", "testing", "portability", "style", "design", "other")
MIN_NOTE_CHARS = 20


def check_app(app_dir: Path) -> list[str]:
    content = app_dir / "content"
    arc_path = content / "archive.json"
    if not arc_path.is_file():
        return []
    name = app_dir.name
    problems: list[str] = []
    try:
        arc = json.loads(arc_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{name}: archive.json 不是合法 JSON：{e}"]
    cur_path = content / "curriculum.json"
    main_ids: set[str] = set()
    if cur_path.is_file():
        cur = json.loads(cur_path.read_text(encoding="utf-8"))
        main_ids = {t["id"] for ch in cur.get("chapters", []) for t in ch.get("topics", [])}

    seen: set[str] = set()
    used_cases: set[str] = set()
    for ch in arc.get("chapters", []):
        if ch.get("layer") != "archive":
            problems.append(f"{name}: 归档章 {ch.get('id')} 的 layer 必须是 archive")
        for t in ch.get("topics", []):
            tid = t.get("id", "?")
            if tid in main_ids or tid in seen:
                problems.append(f"{name}: 归档知识点 id {tid} 与已有 id 重复（id 不改嫁，ADR 0129）")
            seen.add(tid)
            for r in t.get("requires", []):
                if r not in main_ids and r not in seen:
                    problems.append(f"{name}: {tid} 的先修 {r} 不存在")
            blocks = [b for b in t.get("lesson", {}).get("blocks", []) if b.get("type") == "archive"]
            if not blocks:
                problems.append(f"{name}: {tid} 没有 archive 块")
            for b in blocks:
                problems += _check_block(content, name, tid, b, used_cases)

    cases_dir = content / "cases"
    if cases_dir.is_dir():
        for d in sorted(cases_dir.glob("arc_*")):
            if d.is_dir() and d.name not in used_cases:
                problems.append(f"{name}: 案例目录 {d.name} 没有任何归档条目引用（孤儿）")
    return problems


def _check_block(content: Path, name: str, tid: str, b: dict, used: set[str]) -> list[str]:
    out: list[str] = []
    case = b.get("case", "")
    case_dir = content / "cases" / case
    if not case.startswith("arc_") or not case_dir.is_dir():
        return [f"{name}: {tid} 的归档案例目录不存在或不以 arc_ 开头：{case!r}"]
    used.add(case)
    if b.get("run") not in RUN_MODES:
        out.append(f"{name}: {tid} 的 run 只能是 {RUN_MODES}")
    origin = b.get("origin") or {}
    for k in ("repo", "path"):
        if not origin.get(k):
            out.append(f"{name}: {tid} 的 origin 缺 {k}")
    if b.get("run") in ("cli", "linux-only") and not b.get("sources"):
        out.append(f"{name}: {tid} 声明可运行（{b.get('run')}）却没有 sources")
    for src in b.get("sources", []):
        if not (case_dir / src).is_file():
            out.append(f"{name}: {tid} 的源文件不存在：{case}/{src}")
    notes = b.get("notes") or []
    if not notes:
        out.append(f"{name}: {tid} 没有批注——归档条目的价值就在于指出不足（ADR 0176）")
    counts: dict[str, int] = {}
    for n in notes:
        f = case_dir / n.get("file", "")
        if not f.is_file():
            out.append(f"{name}: {tid} 的批注指向不存在的文件：{n.get('file')}")
            continue
        if n["file"] not in counts:
            counts[n["file"]] = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
        end = n.get("end", n.get("line", 0))
        if not (1 <= n.get("line", 0) <= end <= counts[n["file"]]):
            out.append(f"{name}: {tid} 的批注行号越界：{n['file']}:{n.get('line')}-{end}（共 {counts[n['file']]} 行）")
        if n.get("kind") not in NOTE_KINDS:
            out.append(f"{name}: {tid} 的批注 kind 不合法：{n.get('kind')!r}")
        if len(n.get("text", "")) < MIN_NOTE_CHARS:
            out.append(f"{name}: {tid} 的批注太短，说不清问题：{n['file']}:{n.get('line')}")
    return out


def run(repo_root: Path, app_roots: list[str]) -> int:
    problems: list[str] = []
    checked = 0
    for root in app_roots:
        base = repo_root / root
        if not base.is_dir():
            continue
        for app in sorted(base.iterdir()):
            if (app / "content" / "archive.json").is_file():
                checked += 1
                problems += check_app(app)
    print(f"归档章节检查：{checked} 个应用有 archive.json", flush=True)
    if problems:
        raise SystemExit("归档章节校验没通过：\n  " + "\n  ".join(problems))
    return checked
