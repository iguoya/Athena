#!/usr/bin/env python3
"""T-102: GTK (C) + gtkmm manifests from Linux/GTK*, GTKMM*.

Writes:
  manifest-gtk.json/.md + verify-gtk.txt
  manifest-gtkmm.json/.md + verify-gtkmm.txt
Read-only over .cache/legacy-src/.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
LEGACY = REPO / ".cache" / "legacy-src" / "Linux"

JUNK_NAMES = {
    "Makefile",
    "Makefile.in",
    "Makefile.am",
    "aclocal.m4",
    "config.guess",
    "config.sub",
    "config.status",
    "config.log",
    "configure",
    "configure.ac",
    "configure.in",
    "depcomp",
    "install-sh",
    "ltmain.sh",
    "missing",
    "compile",
    "libtool",
    "stamp-h1",
    "autoscan.log",
    "autom4te.cache",
    ".gitignore",
}
JUNK_DIR_PARTS = {
    "autom4te.cache",
    "m4",
    "po",
    "build",
    "build-aux",
    ".deps",
    ".libs",
    "Debug",
    "Release",
    "debug",
    "release",
}
JUNK_SUFFIXES = (
    ".o",
    ".lo",
    ".la",
    ".a",
    ".so",
    ".exe",
    ".dll",
    ".ui~",
    ".glade~",
)


def git_ls(prefix: str = "") -> list[str]:
    args = ["git", "-C", str(LEGACY), "ls-files", "-z"]
    if prefix:
        args.append(prefix)
    out = subprocess.check_output(args)
    return [p.replace("\\", "/") for p in out.decode("utf-8", "replace").split("\0") if p]


def git_first(path: str) -> str | None:
    for args in (
        ["log", "--reverse", "--format=%ad", "--date=short", "--", path],
        ["log", "--diff-filter=A", "--format=%ad", "--date=short", "--", path],
    ):
        try:
            out = subprocess.check_output(
                ["git", "-C", str(LEGACY), *args],
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            ).strip()
        except subprocess.CalledProcessError:
            continue
        if out:
            return out.splitlines()[0].strip()
    return None


def norm_hash(p: Path) -> str:
    data = p.read_bytes()
    if b"\0" in data[:4096]:
        return hashlib.sha256(data).hexdigest()
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            t = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return hashlib.sha256(data).hexdigest()
    t = t.replace("\r\n", "\n").replace("\r", "\n").strip()
    return hashlib.sha256(t.encode()).hexdigest()


def is_junk(rel: str) -> bool:
    name = Path(rel).name
    if name in JUNK_NAMES:
        return True
    if name.endswith(".in") and name.startswith("Makefile"):
        return True
    parts = rel.split("/")
    for part in parts[:-1]:
        if part in JUNK_DIR_PARTS:
            return True
        if part.startswith("autom4te"):
            return True
    low = name.lower()
    for suf in JUNK_SUFFIXES:
        if low.endswith(suf):
            return True
    # anjuta project files are IDE metadata
    if low.endswith(".anjuta") or low.endswith(".anjuta_sym_db.db"):
        return True
    if name.endswith(".pc") and "pkgconfig" in rel:
        return True
    return False


def unit_key(rel: str) -> str:
    parts = rel.split("/")
    top = parts[0]
    if top == "GTK":
        if len(parts) == 1:
            return "GTK/__root__"
        child = parts[1]
        if child == "GtkApp":
            # one app unit (may contain subdirs)
            if len(parts) >= 3 and parts[2] in {"po", "m4", "autom4te.cache", "build"}:
                return f"GTK/GtkApp/__junk__/{parts[2]}"
            return "GTK/GtkApp"
        return f"GTK/{child}"
    if top == "GTKMM":
        if len(parts) == 1:
            return "GTKMM/__root__"
        return f"GTKMM/{parts[1]}"
    if top in ("Examples_Gtkmm", "gtkmm-application-template"):
        return f"{top}/__empty__"
    return "/".join(parts[:2])


def detect_gtk_version(files: list[str], domain: str) -> str:
    """Return gtk2 / gtk3 / gtk4 / gtkmm2 / gtkmm3 / gtkmm4 / unknown."""
    # Prefer interface/callbacks (Anjuta) over copyright-only main.c
    ranked = sorted(
        files,
        key=lambda f: (
            0
            if Path(f).name in {"interface.c", "interface.cc", "callbacks.c", "mainwindow.cpp", "mainwindow.h"}
            else 1
            if Path(f).name.startswith("main")
            else 2,
            f,
        ),
    )
    blob = ""
    for f in ranked:
        if Path(f).suffix.lower() not in {".c", ".cpp", ".cc", ".h", ".hpp", ".ui", ".glade"}:
            continue
        p = LEGACY / f
        if not p.is_file():
            continue
        try:
            blob += p.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        if len(blob) > 24000:
            break
    # also peek configure.ac on disk even if classified junk
    unit_root = ""
    for f in files:
        parts = Path(f).parts
        if len(parts) >= 2:
            unit_root = "/".join(parts[:2])
            break
    conf = ""
    if unit_root:
        for cand in (
            LEGACY / unit_root / "configure.ac",
            LEGACY / unit_root / "configure.in",
        ):
            if cand.is_file():
                conf = cand.read_text(encoding="utf-8", errors="ignore")
                break

    if domain == "gtkmm":
        if re.search(r"gtkmm-4|GTKMM_MAJOR_VERSION\s+4", blob + conf):
            return "gtkmm4"
        if re.search(r"gtkmm-2\.|libgtkmm-2", blob + conf):
            return "gtkmm2"
        if (
            "gtkmm-3" in (blob + conf)
            or "libgtkmm-3" in (blob + conf)
            or "gtkmm.h" in blob
            or "gtkmm/" in blob
            or "Gtk::Application" in blob
        ):
            return "gtkmm3"
        return "gtkmm-unknown"

    # GTK C — configure.ac PKG_CHECK_MODULES is authoritative when present
    if re.search(r"gtk4|gtk-4\.0|GTK4", conf):
        return "gtk4"
    if re.search(r"gtk\+-3\.0|gtk-3\.0", conf):
        return "gtk3"
    if re.search(r"gtk\+-2\.0|gtk-2\.0", conf):
        return "gtk2"
    if "gtk_hbox_new" in blob or "GtkHBox" in blob or "GTK_STOCK_" in blob:
        return "gtk2"
    if "GtkApplication" in blob or "gtk_application_new" in blob:
        return "gtk3"
    if re.search(r'#include\s*<gtk/gtk\.h>', blob):
        return "gtk2-or-3"
    if any(f.endswith((".glade", ".ui")) for f in files):
        return "gtk3-glade" if "gtkbuilder" in blob.lower() or "GtkBuilder" in blob else "gtk2-glade"
    return "unknown"


def detect_hints(blob: str) -> str:
    if "gtk_hbox_new" in blob or "GTK_STOCK_" in blob:
        return "gtk2"
    return ""


def quality_notes(files: list[str], ver: str) -> str:
    notes = []
    notes.append(f"静态判断工具链版本≈{ver}")
    for f in files:
        if not f.endswith((".c", ".cpp", ".cc")):
            continue
        p = LEGACY / f
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")[:4000]
        if "gtk_widget_destroy" in t and "g_object_unref" not in t:
            notes.append(f"{Path(f).name}: 偏手工 destroy，缺 g_object_unref 意识")
        if "TODO" in t or "FIXME" in t:
            notes.append(f"{Path(f).name}: 含 TODO/FIXME")
        if re.search(r"\bmain\s*\(", t) and "gtk_init" in t and "g_application_run" not in t and "gtk_main" in t:
            notes.append(f"{Path(f).name}: 旧式 gtk_main 循环")
        break
    # anjuta boilerplate residue
    if any("anjuta" in f.lower() for f in files):
        notes.append("含 Anjuta 工程痕迹")
    if not notes:
        notes.append("练习级：样板目录多、业务代码少")
    return "；".join(notes[:4])


def topic_hint_gtk(unit: str) -> str:
    u = unit.lower()
    rules = [
        (r"glade|ui\.|\.ui", "archive.gtk.glade"),
        (r"grid", "archive.gtk.layout-grid"),
        (r"box|pack|frame|paned|aspect", "archive.gtk.layout-box"),
        (r"dialog", "archive.gtk.dialog"),
        (r"multi.?window|multi_window|multiwindow", "archive.gtk.multiwindow"),
        (r"hello|basicwindow|simple", "archive.gtk.basics"),
        (r"foobar|anjuta|framework|conponent|component", "archive.gtk.scaffold"),
        (r"gtkapp", "archive.gtk.app"),
    ]
    for pat, h in rules:
        if re.search(pat, u):
            return h
    return "archive.gtk.other"


def topic_hint_gtkmm(unit: str) -> str:
    u = unit.lower()
    rules = [
        (r"glade", "archive.gtkmm.glade"),
        (r"frame|paned|aspect|box", "archive.gtkmm.layout"),
        (r"hello", "archive.gtkmm.basics"),
    ]
    for pat, h in rules:
        if re.search(pat, u):
            return h
    return "archive.gtkmm.other"


def slugify(unit: str, prefix: str) -> str:
    s = unit.lower().replace("gtk/", "").replace("gtkmm/", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return f"{prefix}-{s}"[:80]


def fingerprint(unit_dir: str, files: list[str]) -> str:
    h = hashlib.sha256()
    code = [
        f
        for f in files
        if Path(f).suffix.lower() in {".c", ".cpp", ".cc", ".h", ".hpp", ".ui", ".glade", ".xml"}
        or Path(f).name in {"CMakeLists.txt", "meson.build"}
    ]
    # prefer src/ content for anjuta trees
    srcish = [f for f in code if "/src/" in f or f.endswith((".c", ".cpp"))]
    use = sorted(srcish or code)
    for f in use:
        p = LEGACY / f
        if not p.is_file():
            continue
        if f.startswith(unit_dir + "/"):
            within = f[len(unit_dir) + 1 :]
        else:
            within = Path(f).name
        # normalize anjuta: strip project-name prefixes in path noise
        within = re.sub(r"^src/", "src/", within)
        h.update(within.encode())
        h.update(norm_hash(p).encode())
    return h.hexdigest()


def build_domain(prefixes: list[str], domain: str, target: str) -> tuple[list[dict], list[str], dict]:
    scoped = []
    for pref in prefixes:
        scoped.extend(git_ls(pref))
    # empty placeholder dirs mentioned in task
    for empty in ("Examples_Gtkmm", "gtkmm-application-template"):
        if empty in prefixes or domain == "gtkmm":
            # only for gtkmm domain
            pass

    units: dict[str, list[str]] = defaultdict(list)
    junk_files: list[str] = []
    for rel in scoped:
        if is_junk(rel):
            junk_files.append(rel)
            continue
        units[unit_key(rel)].append(rel)

    # empty tracked? still note empty dirs from task scope
    meta = {}
    for uk, files in units.items():
        files = sorted(files)
        unit_dir = uk if not uk.endswith("/__empty__") else uk.split("/")[0]
        # for fingerprint use actual directory under Linux/
        # uk like GTK/g20-box
        fp = fingerprint(uk, files)
        reps = [
            f
            for f in files
            if Path(f).suffix.lower() in {".c", ".cpp", ".cc", ".h"}
        ][:3] or files[:2]
        firsts = [git_first(r) for r in reps]
        firsts = [d for d in firsts if d]
        ver = detect_gtk_version(files, domain)
        meta[uk] = {
            "files": files,
            "fp": fp,
            "first": min(firsts) if firsts else "unknown",
            "ver": ver,
            "n": len(files),
        }

    by_fp: dict[str, list[str]] = defaultdict(list)
    for uk, m in meta.items():
        by_fp[m["fp"]].append(uk)

    manifests = []
    covered = set()

    def cover(fs):
        covered.update(fs)

    for fp, uks in sorted(by_fp.items(), key=lambda x: (-len(x[1]), x[0])):
        uks_sorted = sorted(uks, key=lambda u: (-meta[u]["n"], u))
        can = uks_sorted[0]
        dups = uks_sorted[1:]
        m = meta[can]
        files = m["files"]
        leaf = can.split("/")[-1]

        if "/__junk__/" in can or leaf.startswith("__"):
            manifests.append(
                {
                    "unit": slugify(can, domain),
                    "title": f"元数据/空 {leaf}",
                    "target": target,
                    "verdict": "drop-junk",
                    "canonical": [f"Linux/{can}"],
                    "duplicates": [f"Linux/{u}" for u in dups],
                    "first_commit": m["first"],
                    "files": m["n"],
                    "run": "read-only",
                    "build": "n/a",
                    "build_checked": False,
                    "topic_hint": "n/a",
                    "quality_notes": "容器/空目录",
                    "reason": "非练习单元",
                    "gtk_version": m["ver"],
                }
            )
            cover(files)
            for u in dups:
                cover(meta[u]["files"])
            continue

        # source files (anjuta puts them under src/; simple demos at unit root)
        src_code = [
            f
            for f in files
            if Path(f).suffix.lower() in {".c", ".cpp", ".cc", ".h", ".hpp"}
        ]
        hand = [
            f
            for f in src_code
            if Path(f).name
            not in {
                "main.c",
                "main.cc",
                "main.cpp",
                "callbacks.c",
                "callbacks.h",
                "interface.c",
                "interface.h",
                "support.c",
                "support.h",
            }
        ]
        # glade-generated support/interface often dominate — still keep one copy of the exercise
        # but mark scaffold-heavy
        ver = m["ver"]
        run = "toolchain"  # Windows has no GTK — never cli
        # Prefer read-only when clearly gtk2 ancient and won't port easily
        if ver in {"gtk2", "gtk2-glade", "gtkmm2"}:
            run = "read-only"

        topic = topic_hint_gtk(can) if domain == "gtk" else topic_hint_gtkmm(can)

        # third-party? unlikely in these trees; GtkApp might vendor
        tp_reason = None
        joined = " ".join(files).lower()
        if "gtk-demo" in joined or "gtkmm-demo" in joined:
            tp_reason = "疑似官方 demo 拷贝"

        if tp_reason:
            verdict = "drop-third-party"
            reason = tp_reason
        else:
            verdict = "keep"
            reason = (
                f"内容哈希相同的脚手架重复 {len(dups)} 处；规范版取文件更多者"
                if dups
                else ""
            )

        # if unit has ZERO source files (only leftover), drop-junk
        if not src_code and not any(
            f.endswith((".ui", ".glade")) for f in files
        ):
            verdict = "drop-junk"
            reason = "无源码/界面文件，仅残余"

        entry = {
            "unit": slugify(can, domain),
            "title": leaf,
            "target": target,
            "verdict": verdict,
            "canonical": [f"Linux/{can}"],
            "duplicates": [f"Linux/{u}" for u in dups],
            "first_commit": m["first"],
            "files": m["n"],
            "run": run,
            "build": (
                f"pkg-config --cflags --libs { 'gtk+-3.0' if 'gtk3' in ver else 'gtk4' if 'gtk4' in ver else 'gtk+-2.0' }"
                if domain == "gtk"
                else f"pkg-config --cflags --libs gtkmm-3.0  # detected {ver}; Windows: do not install for this task"
            ),
            "build_checked": False,
            "topic_hint": topic,
            "quality_notes": quality_notes(files, ver)
            + (
                f"；手写源码少（非样板 {len(hand)} / src {len(src_code)}）"
                if domain == "gtk" and src_code
                else ""
            ),
            "gtk_version": ver,
        }
        if reason:
            entry["reason"] = reason
        # extra field ok? schema doesn't forbid extras; keep gtk_version for md
        manifests.append(entry)
        cover(files)
        for u in dups:
            cover(meta[u]["files"])

    # junk aggregate buckets
    junk_by = defaultdict(list)
    for f in junk_files:
        parts = f.split("/")
        bucket = "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
        junk_by[bucket].append(f)
    for bucket, fs in sorted(junk_by.items()):
        manifests.append(
            {
                "unit": f"junk-{slugify(bucket, domain)}",
                "title": f"Anjuta/autotools/po 生成物 {bucket}",
                "target": target,
                "verdict": "drop-junk",
                "canonical": [f"Linux/{bucket}"],
                "duplicates": [],
                "first_commit": "n/a",
                "files": len(fs),
                "run": "read-only",
                "build": "n/a",
                "build_checked": False,
                "topic_hint": "n/a",
                "quality_notes": "configure.ac / Makefile.in / po / autom4te 等生成物",
                "reason": "任务书：Anjuta/Glade 工程生成样板 drop-junk",
                "gtk_version": "n/a",
                "_files": fs,
            }
        )
        cover(fs)

    missing = sorted(set(scoped) - covered)
    # strip private
    for e in manifests:
        e.pop("_files", None)

    return manifests, missing, {"scoped": scoped, "junk_count": len(junk_files), "unit_meta": meta}


def write_outputs(name: str, manifests: list[dict], missing: list[str], stats: dict, intro: list[str]):
    # unique unit ids
    seen = {}
    for e in manifests:
        base = e["unit"]
        if base in seen:
            seen[base] += 1
            e["unit"] = f"{base}-{seen[base]}"
        else:
            seen[base] = 0

    order = {"keep": 0, "drop-third-party": 1, "drop-junk": 2}

    def sk(e):
        return (order.get(e["verdict"], 9), e.get("topic_hint", ""), e["unit"])

    manifests.sort(key=sk)

    # public JSON: keep gtk_version (useful), drop nothing else
    (OUT / f"manifest-{name}.json").write_text(
        json.dumps(manifests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    keeps = [e for e in manifests if e["verdict"] == "keep"]
    lines = [
        f"# {name.upper() if name!='gtkmm' else 'gtkmm'} 领域清单摘要（T-102）",
        "",
        f"- 生成：{datetime.now().isoformat(timespec='seconds')}",
        *intro,
        "",
        "## 统计",
        "",
        f"| 项 | 数量 |",
        f"|---|---:|",
        f"| 单元 | {len(manifests)} |",
        f"| keep | {len(keeps)} |",
        f"| drop-third-party | {sum(1 for e in manifests if e['verdict']=='drop-third-party')} |",
        f"| drop-junk | {sum(1 for e in manifests if e['verdict']=='drop-junk')} |",
        f"| 生成物文件（drop-junk 桶内） | {stats['junk_count']} |",
        f"| scoped 文件 | {len(stats['scoped'])} |",
        f"| 覆盖遗漏 | {len(missing)} |",
        "",
        "### keep 版本分布（静态判断）",
        "",
    ]
    vc = Counter(e.get("gtk_version", "?") for e in keeps)
    lines += ["| version | n |", "|---|---:|"]
    for v, n in vc.most_common():
        lines.append(f"| `{v}` | {n} |")
    lines += ["", "### topic_hint", "", "| hint | n |", "|---|---:|"]
    for t, n in Counter(e["topic_hint"] for e in keeps).most_common():
        lines.append(f"| `{t}` | {n} |")

    lines += ["", "## keep 一览", ""]
    for e in keeps:
        d = f"（dup {len(e.get('duplicates') or [])}）" if e.get("duplicates") else ""
        lines.append(
            f"- `{e['unit']}` — {e['title']} ← `{e['canonical'][0]}` "
            f"ver={e.get('gtk_version')} run={e['run']} files={e['files']} first={e['first_commit']}{d}"
        )
        lines.append(f"  - {e.get('quality_notes','')}")

    lines += ["", "## 待裁决", ""]
    if name == "gtk":
        lines += [
            "1. 大量 Anjuta 脚手架工程（g17–g38、gtk-foobar…）业务代码几乎只有 callbacks 空壳：是 keep 作「历史脚手架标本」还是大量 merge/drop？",
            "2. 静态判断多为 gtk2/gtk3；`practice/c-gui-lab` 现为 **GTK4 + libadwaita**。建议归档条目全部 `read-only` 或 `toolchain`（需 GTK3），**不要**假装能并进现有 gtk-style 可运行画廊。",
            "3. `Linux/SDL` 由 leader 划给 c-gui-lab——本清单未收录 SDL；若要我补核对另开任务。",
        ]
    else:
        lines += [
            "1. `Examples_Gtkmm/` 与 `gtkmm-application-template/` 在仓库中为空目录（0 tracked / 0 on-disk files），仅作记录。",
            "2. 旧练习为 gtkmm3 形态；`guide/gtkmm` 是官方 gtkmm4 教程翻译——互不引用。归档进新建 `programming/gtkmm-lab` 是否只收「有手写逻辑」的单元？",
            "3. Windows 无 gtkmm 开发库：一律未实测编译（`build_checked: false`），符合任务书。",
        ]

    (OUT / f"manifest-{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    vlines = [
        f"generated: {datetime.now().isoformat(timespec='seconds')}",
        f"scoped_files: {len(stats['scoped'])}",
        f"missing_files: {len(missing)}",
        f"units: {len(manifests)}",
        f"keep: {len(keeps)}",
        f"drop-third-party: {sum(1 for e in manifests if e['verdict']=='drop-third-party')}",
        f"drop-junk: {sum(1 for e in manifests if e['verdict']=='drop-junk')}",
        f"junk_template_files: {stats['junk_count']}",
        "",
        "=== missing ===",
    ]
    vlines += [f"  {m}" for m in missing[:50]] or ["  (none)"]
    (OUT / f"verify-{name}.txt").write_text("\n".join(vlines) + "\n", encoding="utf-8")

    unit_files = {}
    for uk, m in stats["unit_meta"].items():
        unit_files[uk] = [f"Linux/{p}" for p in m["files"]]
    (OUT / f"_{name}_unit_files.json").write_text(
        json.dumps({"missing": [f"Linux/{m}" for m in missing], "by_unit_key": unit_files}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def main():
    print("GTK…")
    gtk_m, gtk_miss, gtk_st = build_domain(["GTK/"], "gtk", "practice/c-gui-lab")
    write_outputs(
        "gtk",
        gtk_m,
        gtk_miss,
        gtk_st,
        [
            "- 目标：`practice/c-gui-lab`（现有，GTK4 画廊；旧代码多为 GTK2/3 → 建议 read-only/toolchain）",
            "- 范围：`Linux/GTK/`",
            "- 本机 Windows **未安装** GTK 开发库，未尝试编译（任务书要求）",
        ],
    )
    print(f"  units={len(gtk_m)} missing={len(gtk_miss)}")

    print("gtkmm…")
    # include empty dir names in scoped? they have 0 files — add synthetic note units
    mm_m, mm_miss, mm_st = build_domain(["GTKMM/"], "gtkmm", "programming/gtkmm-lab")
    # synthetic empty placeholders
    for empty in ("Examples_Gtkmm", "gtkmm-application-template"):
        mm_m.append(
            {
                "unit": f"gtkmm-empty-{empty.lower().replace('_','-')}",
                "title": f"空目录 {empty}",
                "target": "programming/gtkmm-lab",
                "verdict": "drop-junk",
                "canonical": [f"Linux/{empty}"],
                "duplicates": [],
                "first_commit": "n/a",
                "files": 0,
                "run": "read-only",
                "build": "n/a",
                "build_checked": False,
                "topic_hint": "n/a",
                "quality_notes": "任务书点名，但 git 与磁盘均为 0 文件",
                "reason": "空目录占位",
                "gtk_version": "n/a",
            }
        )
    write_outputs(
        "gtkmm",
        mm_m,
        mm_miss,
        mm_st,
        [
            "- 目标：**新建** `programming/gtkmm-lab`（与 `guide/gtkmm` 官方手册精读互不引用）",
            "- 范围：`Linux/GTKMM/`；`Examples_Gtkmm/`、`gtkmm-application-template/` 为空",
            "- 对照：`guide/gtkmm` = gtkmm4 教程翻译；本清单旧练习 ≈ gtkmm3",
            "- 本机未装 gtkmm，未编译",
        ],
    )
    print(f"  units={len(mm_m)} missing={len(mm_miss)}")

    # c-gui-lab placement note file
    (OUT / "note-c-gui-lab-placement.md").write_text(
        "\n".join(
            [
                "# 历史 GTK 条目相对 practice/c-gui-lab 的落点建议",
                "",
                "## 现状（只读 AGENTS.md）",
                "",
                "- `practice/c-gui-lab` 是 **practice** 应用：Electron 母体 + `apps/gtk-style`（**GTK4 + libadwaita**）、imgui、lvgl 等并排对比。",
                "- **不建进度库**；目标是「能跑的对比」，不是课程章节。",
                "",
                "## 旧 Linux/GTK 代码",
                "",
                "- 静态判断以 **GTK2 / GTK3 + Anjuta/Glade 脚手架** 为主（`gtk_main` / `GtkHBox` / `.glade` / `callbacks.c` 样板）。",
                "- 与现网 `apps/gtk-style`（GTK4）**不能直接并入可运行画廊**。",
                "",
                "## 建议",
                "",
                "1. 若 c-gui-lab 增加「历史归档」区：条目一律 `run: read-only` 或 `toolchain`（需自备 GTK3），不要挂进母体一键 spawn。",
                "2. 脚手架重复（内容哈希相同的 g17/g19/…）只留一份规范版，其余 duplicates。",
                "3. 真正有手写逻辑的（如 `GtkApp`、少量非空 callbacks）优先 keep；纯 Anjuta 空壳可考虑 leader 裁决批量 drop。",
                "4. `Linux/SDL` 不在本任务范围；leader 已划给 c-gui-lab，与 GTK 清单分开。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("done")


if __name__ == "__main__":
    main()
