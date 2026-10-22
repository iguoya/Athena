# -*- coding: utf-8 -*-
"""T-104：gtkmm-lab / gtk-c 历史归档暂存包。只写 staging，不改 legacy-src。"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SRC = REPO / ".cache" / "legacy-src"
HERE = Path(__file__).resolve().parent
ART = REPO / "comms" / "legacy-archive" / "artifacts" / "cursor"

SKIP_SUFFIXES = (
    ".user", ".depend", ".layout", ".o", ".obj", ".exe", ".dll", ".so",
    ".dylib", ".a", ".lib", ".pch", ".pdb", ".ilk", ".exp", ".db",
)
SKIP_NAME_PARTS = (".pro.user", ".user.", ".anjuta_sym", ".bak", ".lck")
SKIP_DIRS = {
    "build", "debug", "release", "Debug", "Release", ".git", "CMakeFiles",
    "__pycache__", "autom4te.cache", ".anjuta", "po",
}
MAX_BYTES = 256 * 1024

CHAPTER_SUMMARY = (
    "从旧 Linux 仓库里的 GTK / gtkmm 练习中精选而来（ADR 0176）："
    "代码原样保留，应用内只读（run=toolchain 或 read-only），"
    "另有行级批注指出写法与程序组织上的不足（含 GTK2/3→4、gtkmm3→4 可移植性）。"
    "本章不属于主线，不计入进度，留待人工审视后决定并入、保留或删除。"
)


def should_skip(rel: Path) -> bool:
    name = rel.name
    if name.endswith(SKIP_SUFFIXES):
        return True
    low = str(rel).replace("\\", "/")
    for part in SKIP_NAME_PARTS:
        if part in low:
            return True
    for p in rel.parts:
        if p in SKIP_DIRS:
            return True
    # autotools boilerplate
    if name in {
        "configure", "config.guess", "config.sub", "ltmain.sh", "depcomp",
        "missing", "install-sh", "compile", "aclocal.m4", "config.h.in",
        "intltool-extract.in", "intltool-merge.in", "intltool-update.in",
    }:
        return True
    return False


def first_commit(repo: str, path: str) -> str:
    r = SRC / repo
    cmd = [
        "git", "-C", str(r), "log", "--follow", "--format=%ad",
        "--date=short", "--", path if path != "." else ".",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            return out.splitlines()[-1]
    except Exception:
        pass
    return "unknown"


def copy_tree_filtered(src_dir: Path, dst_dir: Path) -> list[str]:
    copied: list[str] = []
    if not src_dir.exists():
        return copied
    if src_dir.is_file():
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        if src_dir.stat().st_size <= MAX_BYTES and not should_skip(Path(src_dir.name)):
            shutil.copy2(src_dir, dst_dir)
            return [dst_dir.name]
        return []
    for p in sorted(src_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src_dir)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if should_skip(rel):
            continue
        if p.stat().st_size > MAX_BYTES:
            continue
        dest = dst_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        copied.append(rel.as_posix())
    return copied


def list_sources(case_dir: Path) -> list[str]:
    prefer: list[str] = []
    for pat in ("*.cpp", "*.cc", "*.c", "*.h", "*.hpp", "*.ui", "*.glade", "CMakeLists.txt"):
        for p in sorted(case_dir.rglob(pat)):
            if should_skip(p.relative_to(case_dir)):
                continue
            prefer.append(p.relative_to(case_dir).as_posix())
    mains = [s for s in prefer if Path(s).name in ("main.cpp", "main.cc", "main.c")]
    rest = [s for s in prefer if s not in mains]
    return (mains + rest)[:40]


def validate_notes(case_dir: Path, notes: list[dict]) -> list[str]:
    problems = []
    kinds = set()
    if len(notes) < 3:
        problems.append(f"{case_dir.name}: notes < 3")
    for n in notes:
        kinds.add(n.get("kind"))
        f = case_dir / n["file"]
        if not f.is_file():
            problems.append(f"{case_dir.name}: missing {n['file']}")
            continue
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        end = n.get("end", n["line"])
        if not (1 <= n["line"] <= end <= len(lines)):
            problems.append(
                f"{case_dir.name}: bad line {n['file']}:{n['line']}-{end} (n={len(lines)})"
            )
        if len(n.get("text", "")) < 20:
            problems.append(f"{case_dir.name}: short note")
    if len(kinds) < 2:
        problems.append(f"{case_dir.name}: kinds < 2")
    return problems


def topic_shell(
    *,
    tid: str,
    title: str,
    difficulty: int,
    guide_line: str,
    outline: dict,
    lead: str,
    case: str,
    sources: list[str],
    std: str,
    run: str,
    run_note: str,
    summary: str,
    origin: dict,
    notes: list[dict],
    callout: str,
) -> dict:
    return {
        "id": tid,
        "title": title,
        "difficulty": difficulty,
        "mastery_goal": "understand",
        "knowledge_type": "skill",
        "requires": [],
        "track": "archive",
        "guide_line": guide_line,
        "weight": "了解",
        "outline": outline,
        "lesson": {
            "blocks": [
                {"type": "lead", "text": lead},
                {
                    "type": "archive",
                    "case": case,
                    "sources": sources,
                    "std": std,
                    "run": run,
                    "run_note": run_note,
                    "summary": summary,
                    "origin": origin,
                    "notes": notes,
                },
                {
                    "type": "callout",
                    "tone": "info",
                    "title": "对照现行讲解",
                    "text": callout,
                },
            ]
        },
    }


def write_archive(app_staging: Path, title: str, topics: list[dict]) -> None:
    content = app_staging / "content"
    content.mkdir(parents=True, exist_ok=True)
    arc = {
        "tracks": [{"id": "archive", "title": "历史归档", "color": "#6a8f7b"}],
        "chapters": [
            {
                "id": "archive",
                "title": title,
                "track": "archive",
                "layer": "archive",
                "summary": CHAPTER_SUMMARY,
                "topics": topics,
            }
        ],
    }
    (content / "archive.json").write_text(
        json.dumps(arc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_dropped(app_staging: Path, rows: list[tuple[str, str]]) -> None:
    lines = [
        "# 未收入历史归档的 keep 单元（drop-trivial）",
        "",
        "原仓库归档后仍可取回。格式：旧路径 — 原因。",
        "",
    ]
    for path, reason in rows:
        lines.append(f"- `{path}` — {reason}")
    lines.append("")
    (app_staging / "content" / "archive-dropped.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# gtkmm-lab
# ---------------------------------------------------------------------------

GTKMM_RUN_NOTE = "需要 gtkmm-3.0（pkg-config）或本机已装的 gtkmm3；旧 API，gtkmm4 中已改（勿对照 guide/gtkmm 正文）"
GTKMM4_RUN_NOTE = "需要 gtkmm-4.0；本目录缺 mainwindow.ui，按路径无法加载；旧练习勿对照 guide/gtkmm 正文"


def build_gtkmm() -> tuple[int, int]:
    staging = HERE / "gtkmm-lab"
    content = staging / "content"
    cases = content / "cases"
    if cases.exists():
        shutil.rmtree(cases)
    cases.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((ART / "manifest-gtkmm.json").read_text(encoding="utf-8"))
    by_unit = {x["unit"]: x for x in manifest}

    # unit -> meta for kept
    kept_specs = [
        {
            "unit": "gtkmm-1-hello",
            "slug": "hello",
            "group": "basics",
            "title": "Hello（手写 Window + Button）",
            "difficulty": 2,
        },
        {
            "unit": "gtkmm-2-glade",
            "slug": "glade",
            "group": "glade",
            "title": "Glade + Gtk::Builder 加载（Anjuta）",
            "difficulty": 2,
            "extra_dup_units": [
                "gtkmm-3-frame",
                "gtkmm-4-paned",
                "gtkmm-5-asspectframe",
            ],
        },
        {
            "unit": "gtkmm-6-box",
            "slug": "box_glade",
            "group": "glade",
            "title": "Glade Box（未连接的点击回调）",
            "difficulty": 2,
        },
        {
            "unit": "gtkmm-7-box",
            "slug": "box_wip",
            "group": "basics",
            "title": "Box 半成品（未限定命名空间的控件）",
            "difficulty": 2,
        },
    ]

    topics = []
    problems = []
    kept_units = set()

    for spec in kept_specs:
        u = by_unit[spec["unit"]]
        canon = u["canonical"][0]
        repo, _, path = canon.partition("/")
        src = SRC / repo / path
        case = f"arc_gtkmmlab_{spec['slug']}"
        dst = cases / case
        copied = copy_tree_filtered(src, dst)
        if not copied:
            raise SystemExit(f"gtkmm: no files for {spec['unit']} from {src}")
        dups = list(u.get("duplicates") or [])
        for eu in spec.get("extra_dup_units") or []:
            dups.append(by_unit[eu]["canonical"][0])
            kept_units.add(eu)  # accounted as merged, not dropped-as-orphan
        kept_units.add(spec["unit"])
        sources = list_sources(dst)
        fc = u.get("first_commit") or first_commit(repo, path)
        notes, outline, lead, summary, guide, callout, run, run_note, std = gtkmm_notes(
            spec["slug"]
        )
        problems += validate_notes(dst, notes)
        topics.append(
            topic_shell(
                tid=f"gtkmmlab.arc.{spec['slug']}",
                title=spec["title"],
                difficulty=spec["difficulty"],
                guide_line=guide,
                outline=outline,
                lead=lead,
                case=case,
                sources=sources,
                std=std,
                run=run,
                run_note=run_note,
                summary=summary,
                origin={
                    "repo": repo,
                    "path": path,
                    "first_commit": fc,
                    "duplicates": dups,
                },
                notes=notes,
                callout=callout,
            )
        )

    # DesignEvolutionCpp（不在 manifest，任务书追加）
    evo_path = "DesignEvolutionCpp"
    evo_src = SRC / "Linux" / evo_path
    evo_case = "arc_gtkmmlab_evolution"
    evo_dst = cases / evo_case
    copied = copy_tree_filtered(evo_src, evo_dst)
    if not copied:
        raise SystemExit("gtkmm: DesignEvolutionCpp empty")
    notes, outline, lead, summary, guide, callout, run, run_note, std = gtkmm_notes(
        "evolution"
    )
    problems += validate_notes(evo_dst, notes)
    topics.append(
        topic_shell(
            tid="gtkmmlab.arc.evolution",
            title="DesignEvolutionCpp（官方示例跟练 + Basic）",
            difficulty=3,
            guide_line=guide,
            outline=outline,
            lead=lead,
            case=evo_case,
            sources=list_sources(evo_dst),
            std=std,
            run=run,
            run_note=run_note,
            summary=summary,
            origin={
                "repo": "Linux",
                "path": evo_path,
                "first_commit": first_commit("Linux", evo_path),
                "duplicates": [],
            },
            notes=notes,
            callout=callout,
        )
    )

    # group order: basics, glade, evolution already appended
    write_archive(staging, "历史归档 · 早年 gtkmm 练习的整理与批注", topics)

    dropped = []
    for x in manifest:
        if x.get("verdict") != "keep":
            continue
        if x["unit"] in kept_units:
            continue
        # 3/4/5 already merged into glade via extra_dup — marked kept_units
        dropped.append(
            (
                x["canonical"][0],
                "与 2-glade 同构的 Anjuta Glade 空壳（仅 UI 文件名不同），已并入 gtkmmlab.arc.glade",
            )
        )
    # If 3/4/5 in kept_units as merged, they shouldn't appear in dropped.
    # They are in kept_units so skipped — good. But we should document them:
    for eu in ("gtkmm-3-frame", "gtkmm-4-paned", "gtkmm-5-asspectframe"):
        dropped.append(
            (
                by_unit[eu]["canonical"][0],
                "drop-trivial / merge-into gtkmmlab.arc.glade：main.cc 与 2-glade 同构，仅 UI 不同",
            )
        )
    write_dropped(staging, dropped)

    if problems:
        raise SystemExit("gtkmm notes invalid:\n  " + "\n  ".join(problems))
    return len(topics), len(dropped)


def gtkmm_notes(slug: str):
    callout = "新建应用 `programming/gtkmm-lab` 主线尚未落定；批注只标旧 API 事实，不引用 guide/gtkmm 正文。"
    if slug == "hello":
        notes = [
            {
                "file": "main.cpp",
                "line": 6,
                "kind": "portability",
                "text": "`Gtk::Application::create(argc, argv, id)` 是 gtkmm3 风格；gtkmm4 改为无 argc/argv 的 `create(id)`，再 `app->run(argc, argv)`。旧 API，4 中已改。",
            },
            {
                "file": "mainwindow.cpp",
                "line": 8,
                "kind": "portability",
                "text": "`set_border_width(10)` 在 gtkmm4 / GTK4 已移除，边距改用 CSS 或 `set_margin_*`。旧 API，4 中已改。",
            },
            {
                "file": "mainwindow.cpp",
                "line": 16,
                "kind": "portability",
                "text": "`add(m_button)` 把按钮直接塞进 `Gtk::Window` 是 gtkmm3 写法；gtkmm4 窗口不再是容器，要用 `set_child`。旧 API，4 中已改。",
            },
            {
                "file": "mainwindow.cpp",
                "line": 12,
                "end": 13,
                "kind": "design",
                "text": "`signal_clicked().connect(sigc::mem_fun(...))` 连接正确；回调只 `cout`，适合当「信号进成员函数」的最小样例，但没有把业务从窗口类拆出去。",
            },
        ]
        return (
            notes,
            {
                "promise": "看懂 gtkmm3 手写窗口 + 按钮信号的最小闭环。",
                "pain": "能跑不等于可迁移：`create(argc,argv,…)`、`add`、`set_border_width` 在 gtkmm4 都已变。",
                "model": "`MainWindow` 持有 `Gtk::Button`，构造里 connect 并 `add`。",
                "scope": "单窗口单按钮，无布局管理器。",
                "judgment": "作「手写控件」入门样例保留；迁 4 时先改窗口父子关系。",
                "landing": "能指出至少三处 gtkmm3→4 差异，并说出信号连接本身没问题。",
            },
            "点按钮应在控制台打印 `Hello World`；对照批注看哪些 API 在 gtkmm4 已改。",
            "gtkmm3 风格 Hello：`Application::create(argc,argv,id)` + 窗口 `add(button)`。",
            "[基础] 手写 Window/Button，批注抓 gtkmm3→4。",
            callout,
            "toolchain",
            GTKMM_RUN_NOTE,
            "c++17",
        )
    if slug == "glade":
        notes = [
            {
                "file": "src/main.cc",
                "line": 41,
                "kind": "portability",
                "text": "`Gtk::Main kit(argc, argv)` 是 gtkmm2/3 的全局主循环封装；gtkmm4 用 `Gtk::Application`。旧 API，4 中已改。",
            },
            {
                "file": "src/main.cc",
                "line": 35,
                "kind": "portability",
                "text": "`UI_FILE` 写死相对路径 `src/2_glade.ui`，工作目录不在工程根时 `create_from_file` 必失败；应相对可执行文件或用资源嵌入。",
            },
            {
                "file": "src/main.cc",
                "line": 59,
                "kind": "ownership",
                "text": "`get_widget(\"main_window\", main_win)` 取出裸指针后未设删除策略；`kit.run(*main_win)` 结束时谁 delete 窗口不清晰，依赖 Builder 持有期。",
            },
            {
                "file": "src/main.cc",
                "line": 48,
                "end": 55,
                "kind": "design",
                "text": "只加载 UI、不连接任何信号，等于 Anjuta/Glade 向导空壳；3-frame/4-paned/5-asspectframe 的 `main.cc` 同构，仅 UI 文件名不同，故合并为本条。",
            },
        ]
        return (
            notes,
            {
                "promise": "看清 Anjuta 生成的「只加载 .ui」最小程序。",
                "pain": "同构脚手架复制多份，看起来像多个项目，实际没有业务回调。",
                "model": "`Gtk::Main` + `Builder::create_from_file` + `get_widget` + `kit.run`。",
                "scope": "无信号连接；UI 差异见同主题 duplicates。",
                "judgment": "保留一条作脚手架标本，其余路径进 duplicates / dropped。",
                "landing": "能说明为何不能把每个 Anjuta 工程都当独立教学内容。",
            },
            "能启动出空窗口即可；注意工作目录与 `UI_FILE` 相对路径。",
            "Anjuta gtkmm3 Glade 加载器；3/4/5 同构已合并进 duplicates。",
            "[Glade] Anjuta 空壳加载器，批注抓 Gtk::Main 与路径。",
            callout,
            "toolchain",
            GTKMM_RUN_NOTE,
            "c++17",
        )
    if slug == "box_glade":
        notes = [
            {
                "file": "src/main.cc",
                "line": 37,
                "end": 39,
                "kind": "design",
                "text": "定义了 `on_button_clicked` 却从未 `signal_clicked().connect`，也未交给 Builder 自动连；按钮点了不会进这个函数。",
            },
            {
                "file": "src/main.cc",
                "line": 44,
                "kind": "portability",
                "text": "仍用 `Gtk::Main`；与 2-glade 同属 gtkmm3 主循环，gtkmm4 应换 `Gtk::Application`。旧 API，4 中已改。",
            },
            {
                "file": "src/main.cc",
                "line": 59,
                "kind": "coupling",
                "text": "界面全在 `.ui`，回调却写在 `main.cc` 且未挂上——UI 与逻辑「看起来分开」实际断线，比完全没回调更误导。",
            },
        ]
        return (
            notes,
            {
                "promise": "识别「写了回调却没连接」的半成品 Glade 练习。",
                "pain": "读代码以为点按钮会打印 hello，运行却无反应。",
                "model": "Builder 加载窗口 + 游离的 `on_button_clicked`。",
                "scope": "在 2-glade 之上多一个未使用函数。",
                "judgment": "单独成条，专门批「断线回调」。",
                "landing": "能指出应用 `get_widget` 取按钮再 `connect`，或在 Glade 里填 handler 名。",
            },
            "若 UI 里有按钮，点击前请先确认是否已 connect；本例默认不会打印。",
            "与 2-glade 同构，额外有一个从未连接的 `on_button_clicked`。",
            "[Glade] 未连接的点击回调。",
            callout,
            "toolchain",
            GTKMM_RUN_NOTE,
            "c++17",
        )
    if slug == "box_wip":
        notes = [
            {
                "file": "mainwindow.h",
                "line": 21,
                "end": 23,
                "kind": "naming",
                "text": "成员写成 `Fixed fixed`、`ScrolledWindow scrollWindow`、`Label label`，未加 `Gtk::` 前缀；在未 `using` 的情况下不能通过编译（应 `Gtk::Fixed` 等）。",
            },
            {
                "file": "mainwindow.cpp",
                "line": 7,
                "end": 22,
                "kind": "design",
                "text": "构造函数里原先 Hello 逻辑整段注释掉，窗口为空；`on_button_clicked` 仍保留却无连接，属于未完成试验。",
            },
            {
                "file": "mainwindow.h",
                "line": 6,
                "kind": "style",
                "text": "同时 `#include <gtkmm/button.h>` 与 `#include <gtkmm.h>`，后者已拉全库，前者冗余；头文件应只留需要的声明。",
            },
            {
                "file": "main.cpp",
                "line": 6,
                "kind": "portability",
                "text": "与 1-Hello 相同的 gtkmm3 `Application::create(argc, argv, id)`；迁 4 时同样要改。旧 API，4 中已改。",
            },
        ]
        return (
            notes,
            {
                "promise": "把「半成品 / 写到一半编不过」当作可教材料。",
                "pain": "类型名缺命名空间、构造被掏空，比 Hello 更接近真实练习现场。",
                "model": "声明了 Fixed/ScrolledWindow/Label，但构造未装配。",
                "scope": "不能当可运行范例；`run` 仍 toolchain，依赖本机 gtkmm3 时也过不了编译。",
                "judgment": "保留以展示常见半成品错误。",
                "landing": "能说出至少两处导致无法成型的原因。",
            },
            "预期难以干净编译：先看 `mainwindow.h` 的类型名与被注释的构造。",
            "未完成的 Box 试验：缺 `Gtk::` 限定，构造逻辑被注释。",
            "[基础] 半成品 Box，批注抓命名空间与空构造。",
            callout,
            "read-only",
            "原代码声明 `Fixed`/`ScrolledWindow`/`Label` 未加 `Gtk::`，构造又被注释，预期无法按现状编译通过；需要 gtkmm3 头文件方可对照阅读。",
            "c++17",
        )
    if slug == "evolution":
        notes = [
            {
                "file": "main.cpp",
                "line": 21,
                "kind": "portability",
                "text": "`add_from_file(\"../mainwindow.ui\")`：本目录没有 `mainwindow.ui`，相对上级的路径在仓库里也对不上——运行必进 `FileError`。应把 UI 放进工程并改相对可执行文件的路径。",
            },
            {
                "file": "main.cpp",
                "line": 40,
                "kind": "portability",
                "text": "`get_widget<Gtk::Window>(\"window\")` 是 gtkmm4 模板取值写法；与 GTKMM/1-Hello 的 gtkmm3 `get_widget(name, ptr)` 不同代。旧练习混代时不要当同一套 API。",
            },
            {
                "file": "main.cpp",
                "line": 12,
                "kind": "portability",
                "text": "`set_visible(false)` 结束 `Application::run` 是 gtkmm4 习惯；gtkmm3 常见 `hide()`/`Gtk::Main::quit()`。旧 API 对照要分清代数。",
            },
            {
                "file": "main.cpp",
                "line": 54,
                "kind": "ownership",
                "text": "`signal_hide` 里 `delete pDialog`：窗口由 `new` 隐含？实际来自 Builder，再 `delete` 易与 Builder/Application 所有权冲突；更稳妥是让 Application 管理窗口生命周期。",
            },
            {
                "file": "basic/basic.cpp",
                "line": 8,
                "end": 11,
                "kind": "design",
                "text": "自写 `Basic::hello()` 只打印 `hello`，且 `main.cpp` 完全未包含/调用 `Basic`——CMake 若链上它也是死代码，说明「跟练官方示例」与「自有类」未接上。",
            },
        ]
        return (
            notes,
            {
                "promise": "读一份偏 gtkmm4 的 Builder 激活写法，并看清缺 UI、死代码类。",
                "pain": "官方跟练骨架在，关键 `.ui` 不在本目录；`Basic` 类未接入。",
                "model": "`signal_activate` → Builder → `get_widget<T>` → `add_window`。",
                "scope": "含 CMake 与 basic/，无可用 UI。",
                "judgment": "保留作「演进中的跟练」；批注重点是路径与所有权。",
                "landing": "能说明缺 UI 时运行失败点，以及 `Basic` 为何算未完成集成。",
            },
            "按现状会因找不到 `../mainwindow.ui` 失败；阅读时对照 `get_widget<T>` 与 1-Hello 的 gtkmm3 写法。",
            "gtkmm4 风格 Application+Builder 跟练；缺 UI；自有 Basic 未调用。",
            "[演进] DesignEvolutionCpp，批注抓缺 UI 与 gtkmm4 API。",
            callout,
            "read-only",
            GTKMM4_RUN_NOTE,
            "c++17",
        )
    raise KeyError(slug)


# ---------------------------------------------------------------------------
# gtk-c
# ---------------------------------------------------------------------------

GTK3_NOTE = "需要 GTK3 开发库（pkg-config gtk+-3.0）；含 GtkHBox/gtk_main/gtk_widget_show_all 等旧 API，GTK4 中已改"
GTK2_NOTE = "需要 GTK2 或仍提供废弃符号的 GTK3；`gtk_vbox_new`/`GTK_STOCK_*` 等在 GTK4 中已删除"
GTK_RO_NOTE = "只读对照：原工程依赖 Glade 相对路径或混用 GTK2/3/4 API，不在此保证可编译"


def build_gtk() -> tuple[int, int]:
    staging = HERE / "gtk-c"
    content = staging / "content"
    cases = content / "cases"
    if cases.exists():
        shutil.rmtree(cases)
    cases.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((ART / "manifest-gtk.json").read_text(encoding="utf-8"))
    by_unit = {x["unit"]: x for x in manifest}

    # (unit, slug, group, title, difficulty, extra_dup_units)
    keep = [
        ("gtk-10-hboxandvbox", "hboxvbox", "legacy-api", "GtkVBox + Stock 按钮（GTK2 风格）", 2, []),
        ("gtk-04-gtkbox", "gtkbox", "layout", "GtkBox 横向打包", 2, []),
        ("gtk-23-callback", "callback", "signals", "按钮回调与 user_data", 2, []),
        ("gtk-02-css", "css", "styling", "CssProvider 注入样式", 2, []),
        ("gtk-01-hello", "hello_builder", "app", "GtkApplication + Builder（信号被注释）", 2, []),
        ("gtk-24-glade", "glade_signals", "glade", "手写 Glade 取按钮并连接 pressed", 3, []),
        ("gtk-28-gtklayout", "gtklayout", "glade", "Builder 加载 layout.ui", 2, []),
        ("gtk-18-message", "message", "glade", "Glade 标签与回调改文案", 2, []),
        ("gtk-g28-pack", "grid_pack", "layout", "GtkGrid 官方教程风格打包", 2, ["gtk-g25-box"]),
        ("gtk-g23-hello", "gtk4_mix", "app", "混用 gtk_window_set_child（偏 GTK4）", 3, []),
        ("gtk-g30-app", "drawing", "drawing", "DrawingArea + Cairo 涂鸦", 3, []),
        ("gtk-g29-grid", "glade_cb", "glade", "Anjuta：Glade 回调 hello/guoya", 3, []),
        ("gtk-g34-dialog", "dialog_vbox", "dialogs", "手写「对话框」仍用 gtk_vbox_new", 3, []),
        ("gtk-g32-grid", "dialog_builder", "dialogs", "dialog.c：Builder 弹窗未接 parent", 3, []),
        ("gtk-g36-multiwindow", "multiwindow", "windows", "多窗口练习（含 g37-conponent）", 3, [
            "gtk-g37-multi-window",
            "gtk-g38-multi-window",
        ]),
        ("gtk-g17-anjuta", "anjuta_skeleton", "scaffold", "Anjuta 工程骨架（空壳代表）", 2, [
            "gtk-g19-basicwindow",
            "gtk-g20-box",
            "gtk-g21-framework",
            "gtk-g24-hello",
            "gtk-25-glade",
            "gtk-14-gtk-foobar",
            "gtk-15-gtk-foobar",
            "gtk-gtk-foobar",
            "gtk-g31-mixbox",
            "gtk-g37-conponent",
        ]),
        ("gtk-gtkapp3", "gtkapp3", "app", "GtkApp3：gtk_main + Builder 主窗", 3, []),
    ]

    merged_units = set()
    topics = []
    problems = []

    for unit, slug, group, title, diff, extra in keep:
        u = by_unit[unit]
        canon = u["canonical"][0]
        repo, _, path = canon.partition("/")
        src = SRC / repo / path
        case = f"arc_gtk_{slug}"
        dst = cases / case
        # g28-pack: prefer hand-written main.c tree — still copy whole unit
        copied = copy_tree_filtered(src, dst)
        if not copied:
            raise SystemExit(f"gtk: no files for {unit} from {src}")
        # For grid_pack we use g25-box; also copy g28 main.c notes reference g25.
        # If slug grid_pack and we wanted g28's denser main — g25 is cleaner tutorial.
        dups = list(u.get("duplicates") or [])
        for eu in extra:
            dups.append(by_unit[eu]["canonical"][0])
            merged_units.add(eu)
        merged_units.add(unit)
        notes, outline, lead, summary, guide, callout, run, run_note, std = gtk_notes(slug)
        problems += validate_notes(dst, notes)
        label = {
            "legacy-api": "旧 API",
            "layout": "布局",
            "signals": "信号",
            "styling": "样式",
            "app": "应用结构",
            "glade": "Glade",
            "drawing": "绘制",
            "dialogs": "对话框",
            "windows": "多窗口",
            "scaffold": "脚手架",
        }[group]
        if not guide.startswith("["):
            guide = f"[{label}] {guide}"
        topics.append(
            topic_shell(
                tid=f"gtk.arc.{slug}",
                title=title,
                difficulty=diff,
                guide_line=guide,
                outline=outline,
                lead=lead,
                case=case,
                sources=list_sources(dst),
                std=std,
                run=run,
                run_note=run_note,
                summary=summary,
                origin={
                    "repo": repo,
                    "path": path,
                    "first_commit": u.get("first_commit") or first_commit(repo, path),
                    "duplicates": dups,
                },
                notes=notes,
                callout=callout,
            )
        )

    # stable group order
    group_order = [
        "legacy-api", "layout", "signals", "styling", "app", "glade",
        "drawing", "dialogs", "windows", "scaffold",
    ]
    slug_group = {k[1]: k[2] for k in keep}
    topics.sort(key=lambda t: (
        group_order.index(slug_group[t["id"].split(".")[-1]]),
        t["difficulty"],
        t["id"],
    ))

    write_archive(staging, "历史归档 · 早年 GTK(C) 练习的整理与批注", topics)

    dropped = []
    for x in manifest:
        if x.get("verdict") != "keep":
            continue
        if x["unit"] in merged_units:
            # still list merged ones as drop-trivial merge notes
            if x["unit"] not in {k[0] for k in keep}:
                dropped.append(
                    (
                        x["canonical"][0],
                        "merge-into 已收条目（见对应 origin.duplicates）；Anjuta/同构脚手架不单列",
                    )
                )
            continue
        reason = drop_reason(x)
        dropped.append((x["canonical"][0], reason))
    write_dropped(staging, dropped)

    if problems:
        raise SystemExit("gtk notes invalid:\n  " + "\n  ".join(problems))
    return len(topics), len(dropped)


def drop_reason(x: dict) -> str:
    q = x.get("quality_notes") or ""
    unit = x["unit"]
    if any(k in unit for k in ("hello", "hellogtk", "simplegtk", "compile-hello", "cmakegtk")):
        return "drop-trivial：Hello/空窗级或与已收 hello_builder 重复"
    if "glade" in unit or "Glade" in (x.get("title") or ""):
        return "drop-trivial：Glade 向导壳 / 与已收 glade 条目重复且手写逻辑不足"
    if any(k in unit for k in ("point", "array", "datatype", "struct", "memory", "basic-principle")):
        return "drop-trivial：C 语言基础演示，几乎无 GTK 结构可教"
    if "anjuta" in q.lower() or "手写源码少" in q:
        return "drop-trivial：Anjuta/向导样板，手写回调不足（脚手架见 gtk.arc.anjuta_skeleton）"
    if unit.startswith("gtk-g0") or unit.startswith("gtk-g1"):
        return "drop-trivial：GNOME Builder/Anjuta 生成 application/window 样板，有效逻辑不足"
    return "drop-trivial：读完无法写出 ≥3 条具体批注，或与已收条目重复"


def gtk_notes(slug: str):
    callout = (
        "`practice/c-gui-lab` 现行 `apps/gtk-style` 走 GTK4+libadwaita，与本条旧 GTK2/3 代码不能直接对跑；"
        "批注只标旧 API 与结构问题。"
    )
    if slug == "hboxvbox":
        notes = [
            {
                "file": "main.c",
                "line": 36,
                "kind": "portability",
                "text": "`gtk_vbox_new` 是 GTK2/早 GTK3 API，GTK3 应用 `gtk_box_new(GTK_ORIENTATION_VERTICAL,…)`，GTK4 再改为布局/属性另一套。旧 API，4 中已删。",
            },
            {
                "file": "main.c",
                "line": 39,
                "kind": "portability",
                "text": "`gtk_button_new_from_stock(GTK_STOCK_DIALOG_INFO)` 依赖 Stock 图标项，GTK3.10+ 废弃、GTK4 删除；应 `gtk_button_new_with_label` 或 icon-name。",
            },
            {
                "file": "main.c",
                "line": 48,
                "end": 49,
                "kind": "portability",
                "text": "`gtk_widget_show_all` + `gtk_main` 是经典主循环；GTK4 用 `GtkApplication`/`g_application_run`，且默认可见性模型不同。旧 API，4 中已改。",
            },
            {
                "file": "main.c",
                "line": 13,
                "kind": "ownership",
                "text": "`gtk_dialog_run` 后 `gtk_widget_destroy(dialog)` 正确释放模态框；对比只 `show` 不销毁的写法，这里是好的示范。",
            },
        ]
        return (
            notes,
            {
                "promise": "认出 GTK2 风格盒子、Stock 按钮与 `gtk_main`。",
                "pain": "在现代 GTK4 环境几乎原样编不过。",
                "model": "窗口 → vbox → stock 按钮 → 模态 MessageDialog。",
                "scope": "单文件，无 Builder。",
                "judgment": "作旧 API 标本保留。",
                "landing": "能列出至少三处迁 GTK4 必改点。",
            },
            "点 Info 按钮应弹出 Hello World 对话框；Close 退出主循环。",
            "GTK2 风格 VBox+Stock；`run=toolchain`，需仍提供这些符号的 GTK3。",
            "旧 API 标本：VBox/Stock/gtk_main。",
            callout,
            "toolchain",
            GTK2_NOTE,
            "c11",
        )
    if slug == "gtkbox":
        notes = [
            {
                "file": "main.c",
                "line": 14,
                "kind": "portability",
                "text": "`gtk_box_new` + `gtk_box_pack_start` 是 GTK3 常见写法；GTK4 去掉 `pack_start`，改 `gtk_box_append` 等。旧 API，4 中已改。",
            },
            {
                "file": "main.c",
                "line": 31,
                "kind": "design",
                "text": "`gtk_container_add(window, box)` 前已对子控件逐个 `show`，又对 window `show`——可统一 `gtk_widget_show_all(window)`，减少漏 show。",
            },
            {
                "file": "main.c",
                "line": 16,
                "end": 18,
                "kind": "style",
                "text": "按钮先 `gtk_button_new()` 再 `set_label`，直接 `gtk_button_new_with_label` 更短；两按钮无信号，点了无行为。",
            },
        ]
        return (
            notes,
            {
                "promise": "看横向 GtkBox 手工 pack。",
                "pain": "无回调，交互为空。",
                "model": "HBox 塞两个 Button 和一个 Entry。",
                "scope": "单文件。",
                "judgment": "保留作 pack API 对照。",
                "landing": "能说出 GTK4 用 append 替代 pack_start。",
            },
            "窗口应出现「唱歌」「跳舞」与输入框；点击无逻辑。",
            "GTK3 GtkBox 横向 pack，无信号。",
            "横向 GtkBox 打包。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "callback":
        notes = [
            {
                "file": "main.c",
                "line": 38,
                "kind": "naming",
                "text": "变量叫 `hbox`，实际 `gtk_box_new(GTK_ORIENTATION_VERTICAL, 50)`——名字与方向相反，读代码会误判布局。",
            },
            {
                "file": "main.c",
                "line": 5,
                "end": 21,
                "kind": "design",
                "text": "`hello` 与 `guoya` 函数体完全相同，只是连接时 user_data 字符串不同；应合成一个回调，用 `user_data` 区分前缀。",
            },
            {
                "file": "main.c",
                "line": 53,
                "end": 54,
                "kind": "portability",
                "text": "连接的是 `\"pressed\"` 而非 `\"clicked\"`：按下即触发、含重复 press；GTK4 手势/事件模型又不同。教学上应说明与 clicked 的差异。",
            },
            {
                "file": "main.c",
                "line": 44,
                "end": 51,
                "kind": "design",
                "text": "`button3`/`button4` 加入盒子却未 `g_signal_connect`，点「旅行」「开心」无输出，像半截练习。",
            },
        ]
        return (
            notes,
            {
                "promise": "看 `g_signal_connect` 传 user_data 打印标签。",
                "pain": "命名撒谎、回调复制粘贴、半数按钮未连接。",
                "model": "垂直 GtkBox + 四个按钮，两个连 pressed。",
                "scope": "单文件。",
                "judgment": "作信号入门反例很好。",
                "landing": "能指出命名、重复函数、未连接按钮三处。",
            },
            "点「你好」「郭雅」应 printf；另外两按钮无连接。",
            "演示 user_data；`hbox` 名不副实；两按钮未连。",
            "回调与 user_data。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "css":
        notes = [
            {
                "file": "main.c",
                "line": 8,
                "end": 12,
                "kind": "design",
                "text": "`setCss` 创建 `GtkCssProvider` 并 `add_provider` 后 `unref` provider——正确；但函数从未被 `main` 调用，窗口保持默认样式。",
            },
            {
                "file": "main.c",
                "line": 20,
                "end": 23,
                "kind": "portability",
                "text": "`gtk_init` + `gtk_main` 旧主循环；且只用 `gtk_widget_show` 而非 `show_all`（此处无子控件尚可）。GTK4 应换 Application。",
            },
            {
                "file": "main.c",
                "line": 10,
                "kind": "portability",
                "text": "`gtk_css_provider_load_from_data(..., NULL)` 的 GError 参数在新 API 中签名有变；迁 GTK4 要用对应的 load API 与错误处理。",
            },
        ]
        return (
            notes,
            {
                "promise": "看到 CssProvider 用法骨架。",
                "pain": "样式函数写了却没挂到窗口。",
                "model": "provider → style context → priority USER。",
                "scope": "空窗 + 未调用 setCss。",
                "judgment": "保留作「写了没用上」批注。",
                "landing": "能指出应在 show 前对 window 调 setCss。",
            },
            "目前只是空标题窗口；`setCss` 未被调用。",
            "CssProvider 工具函数未接入 main。",
            "CSS 注入未调用。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "hello_builder":
        notes = [
            {
                "file": "main.c",
                "line": 29,
                "end": 36,
                "kind": "design",
                "text": "三个按钮的 `g_signal_connect` 全部注释掉，只显示窗口——Builder 示例的「交互」被掏空，读者看不到 clicked→回调链。",
            },
            {
                "file": "main.c",
                "line": 23,
                "kind": "portability",
                "text": "`gtk_builder_add_from_file(builder, \"01-hello.ui\", NULL)` 忽略 GError，文件缺失时静默得到空对象，后续强转 window 易崩。",
            },
            {
                "file": "main.c",
                "line": 38,
                "kind": "portability",
                "text": "这里用 `gtk_widget_show` 而不是 `show_all`；若 UI 含子控件在 GTK3 可能漏显示。与同仓库大量 `show_all` 写法不一致。",
            },
            {
                "file": "main.c",
                "line": 52,
                "kind": "design",
                "text": "已用 `GtkApplication`（相对 `gtk_main` 更现代），却把信号注释掉——骨架对、教学内容被关掉，优先恢复 connect 或删掉死函数 `print_hello`/`quit_cb`。",
            },
        ]
        return (
            notes,
            {
                "promise": "对照「Application+Builder」正确骨架与被注释的信号。",
                "pain": "能启动但点不到教程里的 Hello。",
                "model": "activate → Builder → set_application → show。",
                "scope": "官方示例删减版。",
                "judgment": "保留作应用结构入门。",
                "landing": "能恢复三处 connect 或说明为何不应注释。",
            },
            "窗口应出现；按钮信号默认未连接。",
            "GtkApplication+Builder，信号被注释。",
            "Application+Builder 空交互。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "glade_signals":
        notes = [
            {
                "file": "main.c",
                "line": 26,
                "kind": "portability",
                "text": "UI 路径写死 `\"../tiger.glade\"`，对工作目录敏感；失败时只 `printf` 仍继续 `get_object`，可能对 NULL 解引用。",
            },
            {
                "file": "main.c",
                "line": 43,
                "end": 46,
                "kind": "ownership",
                "text": "`g_signal_connect(..., gtk_button_get_label(buttonA))` 把标签字符串指针当 user_data；若标签后来被改或按钮销毁，回调里当 `char*` 用会悬空。应 `g_strdup` 或传稳定常量。",
            },
            {
                "file": "main.c",
                "line": 43,
                "kind": "portability",
                "text": "连 `\"pressed\"` 而非 `\"clicked\"`；且 Builder 未 `connect_signals`，全靠手写——与 Anjuta 自动连回调的习惯混用时易重复连接。",
            },
            {
                "file": "main.c",
                "line": 25,
                "end": 30,
                "kind": "design",
                "text": "创建 Builder 后从未 `g_object_unref(builder)`，窗口又靠 `gtk_main` 长命——Builder 持有的额外引用泄漏到进程结束（小例子可忍，坏习惯）。",
            },
        ]
        return (
            notes,
            {
                "promise": "看手写从 Glade 取多按钮并连接。",
                "pain": "相对路径与 user_data 生命周期。",
                "model": "Builder get_object ×4 + pressed 回调。",
                "scope": "依赖 `../tiger.glade`。",
                "judgment": "有真实手写逻辑，值得收。",
                "landing": "能说明 label 指针作 user_data 的风险。",
            },
            "需在正确工作目录找到 `tiger.glade`；点按钮应走 `say`。",
            "手写 Glade 多按钮 pressed；路径与 user_data 危险。",
            "Glade 手写连接。",
            callout,
            "toolchain",
            GTK3_NOTE + "；需 tiger.glade 相对路径可用",
            "c11",
        )
    if slug == "gtklayout":
        notes = [
            {
                "file": "main.c",
                "line": 9,
                "end": 10,
                "kind": "design",
                "text": "`gtk_builder_new` 在 `gtk_init` 之前——多数情况碰巧可用，但正规顺序应先 `gtk_init` 再碰 GTK 对象。",
            },
            {
                "file": "main.c",
                "line": 18,
                "kind": "portability",
                "text": "`../layout.ui` 相对路径；`add_from_file` 的 error 传 NULL，失败时 window 可能为 NULL 仍 `show_all`。",
            },
            {
                "file": "main.c",
                "line": 21,
                "end": 22,
                "kind": "design",
                "text": "只给 `button1` 连了 `print_hello`，其它控件未查；`print_hello` 无参数匹配检查，适合再批「回调签名应带 widget/user_data」。",
            },
        ]
        return (
            notes,
            {
                "promise": "最小 Builder 加载 + 单按钮回调。",
                "pain": "init 顺序与路径错误处理缺失。",
                "model": "builder → layout.ui → button1 clicked。",
                "scope": "单文件。",
                "judgment": "收作 Glade 最小集。",
                "landing": "能说出 init 顺序与 error 检查。",
            },
            "依赖 `../layout.ui`；点 button1 应打印 hello。",
            "Builder 加载 layout.ui。",
            "layout.ui 最小回调。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "message":
        notes = [
            {
                "file": "main.c",
                "line": 3,
                "kind": "coupling",
                "text": "全局 `GtkWidget *label` 供回调改文案——窗口一多或测回调时难隔离；应放 user_data 或对象结构体。",
            },
            {
                "file": "main.c",
                "line": 11,
                "end": 15,
                "kind": "portability",
                "text": "`ui.glade` + `gtk_builder_connect_signals`：依赖把回调符号导出给 Glade（Windows 上常要额外导出宏）；失败时无检查。",
            },
            {
                "file": "main.c",
                "line": 34,
                "kind": "design",
                "text": "`on_btnhello_clicked` 把标签固定写成 `Hello, world!`，不读按钮或计数；与注释掉的计数器逻辑相比，交互过薄但尚能演示 Glade 回调名约定。",
            },
        ]
        return (
            notes,
            {
                "promise": "看 Glade 回调改 Label。",
                "pain": "全局 label、路径写死。",
                "model": "connect_signals → on_btnhello_clicked。",
                "scope": "单 glade。",
                "judgment": "收作回调名约定样例。",
                "landing": "能说明为何全局 widget 指针是耦合。",
            },
            "点 Hello 按钮标签应变为 Hello, world!。",
            "Glade 回调改标签；全局 label。",
            "Glade 改文案。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "grid_pack":
        notes = [
            {
                "file": "src/main.c",
                "line": 70,
                "end": 75,
                "kind": "portability",
                "text": "注释与调用仍强调 `gtk_widget_show_all`——GTK4 删除 `show_all`，控件默认可见策略不同。旧 API，4 中已改。",
            },
            {
                "file": "src/main.c",
                "line": 63,
                "kind": "design",
                "text": "`g_signal_connect_swapped(..., gtk_widget_destroy, window)` 是常见 Quit 写法；比再包一层回调清晰，可作正面批注。",
            },
            {
                "file": "src/main.c",
                "line": 21,
                "kind": "portability",
                "text": "`gtk_container_set_border_width` 在 GTK4 移除；边距改 CSS/`set_margin_*`。旧 API，4 中已改。",
            },
            {
                "file": "src/main.c",
                "line": 47,
                "end": 59,
                "kind": "naming",
                "text": "多个按钮标签都写 `\"Button 3\"`，网格里无法从文案区分单元格；应 Button 3/4/5 或按行列命名。",
            },
        ]
        return (
            notes,
            {
                "promise": "读官方风格 GtkGrid + GtkApplication。",
                "pain": "仍停留在 GTK3 show_all/border_width；标签重复。",
                "model": "activate 里 grid_attach 多按钮 + Quit 跨列。",
                "scope": "g25-box 等同构教程已并入 duplicates；目录内 Anjuta 壳可忽略。",
                "judgment": "布局主线样例。",
                "landing": "能对照 GTK4 删 show_all 的迁移点。",
            },
            "点 Button 打印 Hello World；Quit 销毁窗口。",
            "GtkGrid 教程风（g28-pack 的 main.c）；g25-box 并入 duplicates。",
            "GtkGrid 打包。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "gtk4_mix":
        notes = [
            {
                "file": "src/main.c",
                "line": 26,
                "kind": "portability",
                "text": "`gtk_window_set_child` 是 GTK4 API，同文件却仍用 `GtkApplication` 旧 flags 名等混搭；在纯 GTK3 上编不过，在 GTK4 上又可能缺 `show_all`。版本混用是批注重点。",
            },
            {
                "file": "src/main.c",
                "line": 45,
                "kind": "design",
                "text": "Quit 按钮的 `g_signal_connect_swapped` 整段注释掉，Quit 无功能；比 g25-box 少了闭环。",
            },
            {
                "file": "src/main.c",
                "line": 52,
                "kind": "portability",
                "text": "只用 `gtk_widget_show(window)`：若在 GTK3 且子控件默认不可见，可能只见空窗；与 `set_child` 的 GTK4 语义搅在一起更难排查。",
            },
        ]
        return (
            notes,
            {
                "promise": "识别 GTK3/4 API 混用现场。",
                "pain": "同一文件两边不靠岸。",
                "model": "set_child + grid_attach + 注释掉的 destroy。",
                "scope": "单 main.c。",
                "judgment": "专收作版本混乱标本。",
                "landing": "能判断应整体迁 3 或整体迁 4。",
            },
            "视本机 GTK 版本而定，可能编不过或 Quit 无效。",
            "混用 `gtk_window_set_child` 与教程其它 GTK3 习惯。",
            "GTK3/4 混用。",
            callout,
            "read-only",
            GTK_RO_NOTE,
            "c11",
        )
    if slug == "drawing":
        notes = [
            {
                "file": "src/main.c",
                "line": 28,
                "end": 31,
                "kind": "portability",
                "text": "`gdk_window_create_similar_surface` + `configure-event`/`draw` 是 GTK3 Cairo 习惯；GTK4 改为 snapshot/render 节点，事件也不再是 `GdkEventButton` 这套。旧 API，4 中已改。",
            },
            {
                "file": "src/main.c",
                "line": 4,
                "kind": "ownership",
                "text": "全局 `static cairo_surface_t *surface`：多窗口或关闭后再开时，`close_window` 虽 destroy，但 activate 再进要靠 configure 重建——可测，却让状态逃出窗口对象。",
            },
            {
                "file": "src/main.c",
                "line": 171,
                "end": 173,
                "kind": "design",
                "text": "`gtk_widget_set_events` 补 `BUTTON_PRESS`/`POINTER_MOTION` 才能涂鸦——这是 GTK3 DrawingArea 必做步骤，批注里应肯定：没有这行就「点了没反应」。",
            },
            {
                "file": "src/main.c",
                "line": 185,
                "kind": "portability",
                "text": "`G_APPLICATION_FLAGS_NONE` 在较新 GLib 更名为 `G_APPLICATION_DEFAULT_FLAGS`；属小移植点。",
            },
        ]
        return (
            notes,
            {
                "promise": "读完整 DrawingArea 涂鸦状态机。",
                "pain": "全局 surface；GTK4 需重写事件。",
                "model": "configure 建 surface → draw 贴回 → motion 画刷。",
                "scope": "官方示例级单文件。",
                "judgment": "手写逻辑充足，优先保留。",
                "landing": "能说出 events 掩码与 surface 生命周期。",
            },
            "左键拖动涂鸦，右键清屏；需 GTK3。",
            "Cairo DrawingArea 完整示例。",
            "DrawingArea 涂鸦。",
            callout,
            "toolchain",
            GTK3_NOTE + " + cairo",
            "c11",
        )
    if slug == "glade_cb":
        notes = [
            {
                "file": "src/g29-grid.c",
                "line": 38,
                "end": 49,
                "kind": "design",
                "text": "`hello`/`guoya` 供 Glade `gtk_builder_connect_signals` 按符号名连接；比空壳 Anjuta 多了真回调，但仍只是 `g_print`。",
            },
            {
                "file": "src/g29-grid.c",
                "line": 27,
                "kind": "portability",
                "text": "`UI_FILE` 固定 `src/g29_grid.ui`，从 build 目录启动会找不到；Anjuta 注释里的 `PACKAGE_DATA_DIR` 才是安装布局。",
            },
            {
                "file": "src/g29-grid.c",
                "line": 84,
                "kind": "design",
                "text": "手写 `g_signal_connect(..., hello)` 被注释，依赖 Builder 自动连——若 UI 里 handler 名与 C 符号不一致会静默无反应，排错成本高。",
            },
            {
                "file": "src/g29-grid.c",
                "line": 99,
                "kind": "portability",
                "text": "`gtk_widget_show_all`：旧 API，GTK4 中已改。",
            },
        ]
        return (
            notes,
            {
                "promise": "看 Anjuta+Glade 回调符号约定。",
                "pain": "路径与 handler 名不一致时难查。",
                "model": "G_DEFINE_TYPE Application + connect_signals。",
                "scope": "相对纯空壳多两个 print 回调。",
                "judgment": "代表「有回调的 Anjuta」。",
                "landing": "能说明 Glade 回调名必须匹配 C 符号。",
            },
            "UI 内按钮若绑了 hello/guoya，点击应 g_print。",
            "Anjuta 网格 + Glade 回调。",
            "Glade 回调名约定。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "dialog_vbox":
        notes = [
            {
                "file": "src/g34-dialog.c",
                "line": 53,
                "kind": "portability",
                "text": "`about_dialog_show` 里用 `gtk_vbox_new` 搭「Create DB」窗——在已用 `GtkApplication` 的工程里夹GTK2 API。旧 API，4 中已删。",
            },
            {
                "file": "src/g34-dialog.c",
                "line": 49,
                "end": 58,
                "kind": "ownership",
                "text": "新窗口 `gtk_window_new` 后未 `gtk_window_set_transient_for`、未交给 Application、无销毁策略，关主窗后子窗可能残留或成孤儿。",
            },
            {
                "file": "src/g34-dialog.c",
                "line": 39,
                "end": 43,
                "kind": "design",
                "text": "`hello` 用静态 `num` 计数打印，无 widget 参数——作 Glade 回调时签名也不标准，扩展时难拿按钮状态。",
            },
            {
                "file": "src/g34-dialog.c",
                "line": 106,
                "kind": "portability",
                "text": "主窗仍 `gtk_widget_show_all`。旧 API，4 中已改。",
            },
        ]
        return (
            notes,
            {
                "promise": "看「对话框」实际是再建顶级窗 + vbox。",
                "pain": "Application 工程夹 GTK2 盒子 API。",
                "model": "Builder 主窗 + 手写第二窗。",
                "scope": "Anjuta 应用类 + 手写 about_dialog_show。",
                "judgment": "收作对话框误用标本。",
                "landing": "能说出应用该用 GtkDialog/transient。",
            },
            "若 UI 接到 about_dialog_show，会再开一个无模态的录入窗。",
            "手写第二窗仍用 gtk_vbox_new。",
            "伪对话框 + VBox。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "dialog_builder":
        notes = [
            {
                "file": "src/dialog.c",
                "line": 20,
                "end": 27,
                "kind": "design",
                "text": "`quick_message(parent, message)` 两个参数都未使用：未设 transient、未把 `message` 填进 UI，函数名与行为不符。",
            },
            {
                "file": "src/dialog.c",
                "line": 26,
                "kind": "ownership",
                "text": "`gtk_builder_add_from_file` 后 `get_object` 得到 window 就 `show_all`，Builder 未 `unref`，也未保存指针——每次调用漏一个 Builder。",
            },
            {
                "file": "src/dialog.c",
                "line": 20,
                "kind": "portability",
                "text": "又写死 `src/dialog.ui`；从别的 cwd 启动必失败，且 error 传 NULL。",
            },
            {
                "file": "src/g32-grid.c",
                "line": 60,
                "kind": "design",
                "text": "主程序 `gtk_builder_connect_signals` 后几乎无手写业务；真正有问题的逻辑在 `dialog.c`，说明「多文件」时批注要跟到非 Anjuta 模板文件。",
            },
        ]
        return (
            notes,
            {
                "promise": "追查 dialog.c 名实不符的弹窗辅助函数。",
                "pain": "参数不用、Builder 泄漏、路径写死。",
                "model": "Anjuta 主壳 + 手写 quick_message。",
                "scope": "收 g32 因 dialog.c 有实质问题。",
                "judgment": "对话框反例。",
                "landing": "能重写 quick_message 使 parent/message 生效。",
            },
            "阅读 `dialog.c`；不要期待 message 会显示在 UI 上。",
            "quick_message 忽略参数并泄漏 Builder。",
            "dialog.c 名实不符。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "multiwindow":
        notes = [
            {
                "file": "src/g36-multiwindow.c",
                "line": 27,
                "kind": "portability",
                "text": "主应用加载 `g36_multiwindow.ui`；同目录还有完整的 `g37-conponent` 另一套 Application 类——一个工程塞两个 G_DEFINE_TYPE 应用，链接/激活意图不清。",
            },
            {
                "file": "src/g37-conponent.c",
                "line": 39,
                "end": 42,
                "kind": "naming",
                "text": "文件名 `conponent` 拼写错误（component）；`hello` 回调无参数列表，作 Glade handler 不灵活。",
            },
            {
                "file": "src/g36-multiwindow.c",
                "line": 80,
                "kind": "design",
                "text": "`TODO: Add code here to open the file` 仍在——名为 multiwindow，实际 `open` 只是再 `new_window`，没有多窗协调（谁是主、如何传数据）。",
            },
            {
                "file": "src/g36-multiwindow.c",
                "line": 83,
                "kind": "portability",
                "text": "`gtk_widget_show_all` 旧 API，4 中已改。",
            },
        ]
        return (
            notes,
            {
                "promise": "看「多窗口」命名下实际仍是 Anjuta 单窗模板。",
                "pain": "工程内并列第二套 application 类。",
                "model": "GApplication activate/open → Builder 窗。",
                "scope": "g37/g38 变体并入 duplicates。",
                "judgment": "收一条代表多窗系列。",
                "landing": "能说明真多窗要共享 app、分清窗口角色。",
            },
            "启动应有主窗；不要期待完整多窗协议。",
            "multiwindow 目录含第二套 conponent 应用类。",
            "多窗口空壳系列。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "anjuta_skeleton":
        notes = [
            {
                "file": "src/g17-anjuta.c",
                "line": 80,
                "kind": "design",
                "text": "仍是 `TODO: Add code here to open the file`——典型 Anjuta 向导残留；g19/g20/g21/foobar 等大量同构，故只留本条代表。",
            },
            {
                "file": "src/g17-anjuta.c",
                "line": 52,
                "end": 60,
                "kind": "portability",
                "text": "`gtk_builder_add_from_file` + `gtk_builder_connect_signals`：无业务 handler 时 connect 为空操作；UI 路径 `src/…ui` 依赖 cwd。",
            },
            {
                "file": "src/g17-anjuta.c",
                "line": 83,
                "kind": "portability",
                "text": "`gtk_widget_show_all` 旧 API，4 中已改。",
            },
            {
                "file": "src/main.c",
                "line": 43,
                "end": 44,
                "kind": "ownership",
                "text": "`g_application_run` 后 `g_object_unref(app)` 正确；骨架里这是少数值得保留的习惯。",
            },
        ]
        return (
            notes,
            {
                "promise": "用一条代表几十个 Anjuta 空壳。",
                "pain": "清单 keep 很多，教学内容重复。",
                "model": "G_DEFINE_TYPE + Builder + TODO open。",
                "scope": "duplicates 列出同构路径。",
                "judgment": "宁少勿滥，脚手架只留标本。",
                "landing": "遇到同构目录应 merge 而不是各写条目。",
            },
            "空窗级；用来认 Anjuta 模板结构。",
            "Anjuta 空壳代表；同构目录见 duplicates。",
            "Anjuta 工程骨架标本。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    if slug == "gtkapp3":
        notes = [
            {
                "file": "main.c",
                "line": 50,
                "end": 53,
                "kind": "design",
                "text": "大段 `GtkApplication`/`activate` 被注释，最终退回 `gtk_init`+`gtk_main`——与目录名 GtkApp3、以及 Process/ 子模块想表达的「应用」不一致。",
            },
            {
                "file": "main.c",
                "line": 60,
                "kind": "portability",
                "text": "`gtk_builder_new_from_file(\"ui/mainwindow.glade\")` 写死相对路径；失败无检查直接 `get_object`。",
            },
            {
                "file": "main.c",
                "line": 70,
                "end": 76,
                "kind": "portability",
                "text": "`destroy`→`gtk_main_quit` + `show_all` + `gtk_main`：经典 GTK3 循环。旧 API，4 中已改。",
            },
            {
                "file": "Process/process.c",
                "line": 17,
                "end": 21,
                "kind": "design",
                "text": "`create_task` 只往 TextView append「创建进程.....」，真正的 `fork`/wait 逻辑整段注释——UI 按钮名暗示进程实验，实际无进程。",
            },
        ]
        return (
            notes,
            {
                "promise": "看小型多文件 GTK 工程如何名实偏离。",
                "pain": "Application 路被注释；Process 无进程。",
                "model": "main 开 Builder 主窗 + Glade 信号进 Process。",
                "scope": "比纯 Hello 大，比完整应用小。",
                "judgment": "收作「模块化未完成」样例。",
                "landing": "能指出注释掉的 Application 与假 create_task。",
            },
            "主窗依赖 `ui/mainwindow.glade`；进程相关按钮勿期待真 fork。",
            "GtkApp3：退回 gtk_main；Process 逻辑被注释。",
            "GtkApp3 名实偏离。",
            callout,
            "toolchain",
            GTK3_NOTE,
            "c11",
        )
    raise KeyError(slug)


def main() -> None:
    n1, d1 = build_gtkmm()
    n2, d2 = build_gtk()
    print(f"gtkmm-lab topics={n1} dropped_rows={d1}")
    print(f"gtk-c topics={n2} dropped_rows={d2}")
    # verify
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import archive_check as a

    for name in ("gtkmm-lab", "gtk-c"):
        probs = a.check_app(HERE / name)
        print(name, "OK" if not probs else probs)
        if probs:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
