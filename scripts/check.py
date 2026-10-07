#!/usr/bin/env python3
"""仓库统一验证入口（ADR 0007、0045、0047）。

检查逻辑归各应用自己（subjects/<id>/ 与 practice/<id>/ 下的 scripts/check.py），
这里只负责依次调用，
外加四项跨应用检查：内容必须有出处（ADR 0043），项目 skill 在 .agents/ 与
.claude/ 两处一致（ADR 0061），GitHub 工作流过 actionlint 与变量粘连检查，
结构卫生（文档树对账、应用四件套、ADR 索引覆盖）。新增应用放一份自己的
check.py 就会被带上，不用改这个文件，也不用改 CI。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash
或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py                  跨应用检查 + 每个应用自己的检查
    python3 scripts/check.py cpp [参数...]    只跑某个应用，余下参数透传给它
    python3 scripts/check.py --sources-only   只跑跨应用检查（skill 两处一致 + 出处 + 工作流 + 结构卫生）
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent



def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8，打印中文会抛 UnicodeEncodeError。

    跨平台的做法是在入口处把标准流重设成 UTF-8，而不是把提示改成英文
    或者只在 CI 里设 PYTHONIOENCODING（ADR 0047）。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

# 应用住在这两处，彼此平级（ADR 0060）。按意图分住处，但都走同一个验证入口。
APP_ROOTS = ("subjects", "practice")


def find_app(app: str) -> Path:
    """按目录名找应用。两处同名会让 `check.py <id>` 有歧义，直接报错而不是任选一个。"""
    found = [REPO_ROOT / root / app for root in APP_ROOTS if (REPO_ROOT / root / app).is_dir()]
    if not found:
        raise SystemExit(f"找不到应用 {app}（在 {' 和 '.join(APP_ROOTS)} 下都没有）")
    if len(found) > 1:
        paths = "、".join(str(p.relative_to(REPO_ROOT)) for p in found)
        raise SystemExit(f"应用名 {app} 同时存在于 {paths}，改名消除歧义")
    return found[0]


def run_app(app: str, extra: list[str]) -> None:
    entry = find_app(app) / "scripts" / "check.py"
    if not entry.is_file():
        raise SystemExit(f"应用 {app} 没有 {entry.relative_to(REPO_ROOT)}")
    print(f"== 检查应用：{app} ==", flush=True)
    completed = subprocess.run([sys.executable, str(entry), *extra], cwd=entry.parent.parent)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


# 不参与构建或不是人写的内容，扫了只会制造噪声。
_SKIP_DIRS = {
    ".git", "archive", "build", "builddir", "target", ".build",
    "node_modules", "dist", ".venv", "__pycache__",
}
_SKIP_SUFFIXES = {".db", ".png", ".jpg", ".jpeg", ".ico", ".icns", ".pdf", ".lock"}


def run_skill_mirror_check() -> None:
    """项目 skill 在 .agents/skills/（源）与 .claude/skills/（副本）两处必须逐字一致（ADR 0061）。

    Codex 只读前者，Claude Code 只读后者。不用符号链接：Windows 上 git 默认把它检出成
    普通文本文件（ADR 0047）。只放一处、或两处内容不同，都等于有一个代理拿到的是旧版。
    """
    print("== 跨应用检查：项目 skill 两处一致 ==", flush=True)
    source, mirror = REPO_ROOT / ".agents" / "skills", REPO_ROOT / ".claude" / "skills"

    def files(root: Path) -> dict[Path, bytes]:
        if not root.is_dir():
            return {}
        return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    src, dst = files(source), files(mirror)
    problems = [f"  只在 .agents/skills/：{p}" for p in sorted(src.keys() - dst.keys())]
    problems += [f"  只在 .claude/skills/：{p}" for p in sorted(dst.keys() - src.keys())]
    problems += [f"  内容不同：{p}" for p in sorted(src.keys() & dst.keys()) if src[p] != dst[p]]
    if problems:
        print("\n".join(problems), flush=True)
        raise SystemExit(
            f"项目 skill 两处不一致（{len(problems)} 处）。以 .agents/skills/ 为源，"
            "改完后整目录复制到 .claude/skills/。"
        )


_RUN_BLOCK_RE = re.compile(r"^(?P<indent>\s*)(?:- )?run:\s*(?P<inline>[|>]-?\s*$|.+$)")
_ASSIGN_RE = re.compile(
    r"(?:^|[\s;(&|])(?:(?:export|local|readonly|declare)\s+(?:-\w+\s+)?)?([A-Za-z_]\w*)\+?="
    r"|\bfor\s+([A-Za-z_]\w*)\s+in\b"
    r"|\bread\s+(?:-\w+\s+)*([A-Za-z_]\w*(?:\s+[A-Za-z_]\w*)*)"
)
_PLAIN_REF_RE = re.compile(r"\$([A-Za-z_]\w*)")
_YAML_KEY_RE = re.compile(r"^\s+([A-Za-z_]\w*):", re.MULTILINE)


def _run_blocks(text: str) -> list[tuple[int, str]]:
    """按缩进切出工作流里每个 run 脚本（行号从 1 起），不引入 YAML 解析依赖。"""
    lines = text.splitlines()
    blocks, i = [], 0
    while i < len(lines):
        m = _RUN_BLOCK_RE.match(lines[i])
        if not m:
            i += 1
            continue
        start, body = i + 1, []
        if m.group("inline").strip()[:1] in "|>":
            base = len(m.group("indent"))
            i += 1
            while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > base):
                body.append(lines[i])
                i += 1
        else:
            body.append(m.group("inline"))
            i += 1
        blocks.append((start, "\n".join(body)))
    return blocks


def find_variable_glue(text: str) -> list[str]:
    """找 "$version_amd64" 这类粘连：脚本给 version 赋过值，却引用了从没出现过的
    version_amd64——本意是 ${version}_amd64。actionlint 调 shellcheck 时关掉了
    SC2154（未赋值变量），因为 env: 注入的变量它看不见，这一类就漏了过去。

    只在「整体从没定义、但某个下划线前缀被赋过值」时报，误报很少。
    """
    known = set(_YAML_KEY_RE.findall(text))  # env: 与 with: 的键，粗放地都算已定义
    problems = []
    for start, script in _run_blocks(text):
        assigned = {name for groups in _ASSIGN_RE.findall(script) for g in groups for name in g.split() if name}
        for offset, line in enumerate(script.splitlines()):
            for ref in _PLAIN_REF_RE.findall(line):
                if ref in assigned or ref in known or ref.startswith(("GITHUB_", "RUNNER_")) or "_" not in ref:
                    continue
                parts = ref.split("_")
                prefix = next(
                    ("_".join(parts[:k]) for k in range(len(parts) - 1, 0, -1) if "_".join(parts[:k]) in assigned),
                    None,
                )
                if prefix:
                    rest = ref[len(prefix):]
                    problems.append(f"第 {start + offset} 行：${ref} 从没赋值，本意多半是 ${{{prefix}}}{rest}")
    return problems


def run_workflow_check() -> None:
    """GitHub 工作流：actionlint（含 shellcheck）加变量粘连检查。

    工作流只在 CI 上真跑，写错了要等一轮全量构建才暴露——v9.0.0 的 Linux deb 就是
    "_$version_amd64.deb" 改名失败、上传找不到文件。本地先拦一道。
    """
    print("== 跨应用检查：GitHub 工作流 ==", flush=True)
    missing = [tool for tool in ("actionlint", "shellcheck") if shutil.which(tool) is None]
    if missing:
        raise SystemExit(
            f"缺 {'、'.join(missing)}，工作流检查跑不了。安装：\n"
            "  Windows: winget install rhysd.actionlint；winget install koalaman.shellcheck\n"
            "  macOS:   brew install actionlint shellcheck\n"
            "  Linux:   sudo apt-get install shellcheck；actionlint 用 "
            "go install github.com/rhysd/actionlint/cmd/actionlint@latest"
        )
    workflows = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    completed = subprocess.run(["actionlint", *map(str, workflows)], cwd=REPO_ROOT)
    problems = [
        f"  {wf.relative_to(REPO_ROOT)} {p}" for wf in workflows for p in find_variable_glue(wf.read_text(encoding="utf-8"))
    ]
    if problems:
        print("\n".join(problems), flush=True)
    if completed.returncode != 0 or problems:
        raise SystemExit("工作流检查没通过，见上方。")


def run_source_check() -> None:
    print("== 跨应用检查：内容必须有出处 ==", flush=True)
    node = shutil.which("node")
    if node is None:
        # 不跳过。检查器自己的注释就写着「沉默地通过是最坏的结果」，入口更不该
        # 因为缺个 node 就把整项检查放过去还报通过。node 是开发必备工具，
        # 按仓库基线视为已装；没有就说清楚装什么（AGENTS.md「基线」一节）。
        raise SystemExit("没有 node，跨应用出处检查跑不了。装 Node.js 后重试。")
    completed = subprocess.run(
        [node, "scripts/check-app-sources.mjs"], cwd=REPO_ROOT
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


# 没开工的素材坑连 app.json 都没有（REPOSITORY.md「三类判据」），只要求 README。
_EMPTY_PLOT_MINIMUM = ("README.md",)
# 开工的应用四件套：规则入口、代理入口、验证入口、导航入口。
_APP_MINIMUM = ("AGENTS.md", "CLAUDE.md", "README.md", "scripts/check.py")

_STRUCTURE_TREE_RE = re.compile(r"^  (\S+)/")
_GROUP_RE = re.compile(r"^(subjects|practice)/")

# 仓库根只认这些条目：文档、代理与编辑器配置、六大功能区。别的出现在根下
# 要么登记进来，要么进 .gitignore，要么删——launcher_list_out.txt、
# __pycache__、dist-driver 三次杂物全都堆在根，不是巧合，根是随手一放的地方。
_ROOT_ALLOW = {
    "AGENTS.md", "CLAUDE.md", "README.md", "CHANGELOG.md", "LICENSE",
    ".git", ".gitignore", ".gitattributes", ".zcodeignore",
    ".agents", ".claude", ".cursor", ".gemini", ".vscode", ".github",
    "subjects", "practice", "launcher", "docs", "scripts", "archive",
}

# 本机构建产物：存在就必须被 .gitignore 覆盖。一个新 Tauri 应用的 target 是
# 几个 GB，漏写一行 ignore 就是把磁盘灌进 git 历史，永远删不干净。
_ARTIFACT_PATHS = (
    "src-tauri/target", "node_modules", "target", "build", ".dart_tool",
    ".venv", "engine/.venv", "third_party", "workspace/.vs", "upstream",
)


def _git_ignored(*paths: Path) -> set[Path]:
    """批量问 git 哪些路径被忽略。check-ignore 对被忽略的路径正常输出、退出码 0。

    git 输出的是正斜杠路径，Windows 上 pathlib 的 str() 是反斜杠，直接比对
    字符串会全部判成「未忽略」——先统一成 posix 风格。
    """
    if not paths:
        return set()
    completed = subprocess.run(
        ["git", "check-ignore", "--", *(p.as_posix() for p in paths)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    reported = {line for line in completed.stdout.splitlines() if line}
    return {p for p in paths if p.as_posix() in reported}


def run_structure_check() -> None:
    """结构卫生：文档与目录对账、应用四件套、ADR 索引覆盖。

    项目变大后混乱都不是突然来的，是「加了一个东西、忘了另外三处」攒出来的：
    c 改名 machine 时 REPOSITORY.md 没跟上，gtkmm 进仓库时结构树没写它，
    0082/0087/0088 三篇 ADR 落库时索引漏了行——每处单看都是小事，叠起来就是
    「文档还能不能信」的问题。这里把三类对账变成检查，再犯就在本地拦下。
    """
    print("== 跨应用检查：结构卫生 ==", flush=True)
    problems: list[str] = []

    # 1. REPOSITORY.md 的结构树必须与实际目录一致：树里多写的是幻觉，
    #    少写的是新应用忘了登记——两个方向都算文档漂移。
    #    只解析 ``` 围栏内的树，正文里两空格缩进的普通段落不算数。
    repository_doc = REPO_ROOT / "docs" / "REPOSITORY.md"
    tree: dict[str, set[str]] = {"subjects": set(), "practice": set()}
    group = None
    in_tree_block = False
    for line in repository_doc.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_tree_block = not in_tree_block
            group = None
            continue
        if not in_tree_block:
            continue
        head = _GROUP_RE.match(line)
        if head:
            group = head.group(1)
            continue
        entry = _STRUCTURE_TREE_RE.match(line)
        if entry and group:
            tree[group].add(entry.group(1))
    for root in ("subjects", "practice"):
        actual = {p.name for p in (REPO_ROOT / root).iterdir() if p.is_dir()}
        for ghost in sorted(tree[root] - actual):
            problems.append(f"  {repository_doc.relative_to(REPO_ROOT)} 结构树写了 {root}/{ghost}/，实际没有这个目录")
        for unlisted in sorted(actual - tree[root]):
            problems.append(f"  实际存在 {root}/{unlisted}/，结构树没有登记（加进 docs/REPOSITORY.md）")

    # 2. 应用四件套：有 app.json 的目录是开工的应用，四个人口缺一不可；
    #    没有 app.json 的按素材坑对待，至少要有一份 README 说明它是什么。
    for root in APP_ROOTS:
        for entry in sorted((REPO_ROOT / root).iterdir()):
            if not entry.is_dir():
                continue
            required = _APP_MINIMUM if (entry / "app.json").is_file() else _EMPTY_PLOT_MINIMUM
            for missing in (name for name in required if not (entry / name).is_file()):
                problems.append(f"  {root}/{entry.name} 缺 {missing}")

    # 3. 仓库级 ADR 索引覆盖：落在 docs/decisions/ 的每一篇都必须能从 README
    #    走到（0082/0087/0088 就曾三篇同时漏行，索引成了不全的地图）。
    decisions = REPO_ROOT / "docs" / "decisions"
    index_text = (decisions / "README.md").read_text(encoding="utf-8")
    for adr in sorted(decisions.glob("*.md")):
        if adr.name != "README.md" and f"]({adr.name})" not in index_text:
            problems.append(f"  docs/decisions/{adr.name} 没有出现在索引 README.md 里")

    if problems:
        print("\n".join(problems), flush=True)
        raise SystemExit(f"结构卫生没通过（{len(problems)} 处），见上方。")

    # 4. 仓库根白名单：根下出现既不在白名单、也没被 .gitignore 接管的条目就报。
    #    不直接拒绝白名单外的东西，是给「确实该住根下」的新条目留一条显式登记的路。
    root_entries = {p.name for p in REPO_ROOT.iterdir()}
    strangers = root_entries - _ROOT_ALLOW
    if strangers:
        ignored = _git_ignored(*(REPO_ROOT / name for name in strangers))
        problems += [
            f"  仓库根下的 {name} 既不在白名单也没被忽略——登记进 check.py 的 "
            "_ROOT_ALLOW、写进 .gitignore，或删掉"
            for name in sorted(strangers - {p.name for p in ignored})
        ]

    # 5. 构建产物必须被忽略：每个应用目录下真实存在的产物路径，逐个过
    #    git check-ignore。新应用忘写 .gitignore，几个 GB 的 target 就会等在
    #    第一次 git add 的路上。
    for root in (*APP_ROOTS, "launcher"):
        for app_dir in sorted((REPO_ROOT / root).iterdir()):
            if not app_dir.is_dir():
                continue
            candidates = {
                app_dir / rel
                for rel in _ARTIFACT_PATHS
                if (app_dir / rel).exists()
            }
            unprotected = candidates - _git_ignored(*candidates)
            problems += [
                f"  {p.relative_to(REPO_ROOT)} 是构建产物却没有被 .gitignore 覆盖"
                for p in sorted(unprotected)
            ]

    # 6. 发布矩阵必须先过 CI：release.yml 里构建的每个应用都要能在 ci.yml 的
    #    手动选择清单里找到对应验证。「发出去但从来没人验证过」就是 v9.0.0 之前
    #    六个应用的状态，不允许再来一次。
    release_text = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    options = re.search(r"options:\s*\[([^\]]+)\]", ci_text)
    ci_apps = {name.strip() for name in options.group(1).split(",")} if options else set()
    released = set(re.findall(r"^\s+- app: (\S+)$", release_text, re.MULTILINE))
    released |= set(re.findall(r"^  (driver|ascent):$", release_text, re.MULTILINE))
    for name in sorted(released - ci_apps):
        problems.append(f"  release.yml 构建应用 {name}，但 ci.yml 的 choices 里没有它——发布必须先有验证")

    if problems:
        print("\n".join(problems), flush=True)
        raise SystemExit(f"结构卫生没通过（{len(problems)} 处），见上方。")
    print(
        f"结构树与 {sum(len(v) for v in tree.values())} 个应用目录一致，"
        f"四件套齐备，ADR 索引全覆盖，根目录干净，产物全被忽略，"
        f"发布矩阵 {len(released)} 个应用全部有 CI",
        flush=True,
    )


def main(argv: list[str]) -> int:
    _force_utf8_output()
    # CI 把跨应用检查和各应用检查拆成不同的 job 并行跑，需要单独触发前者；
    # 有了它，CI 的每一步都还是走这一个入口（ADR 0007）。
    if argv[:1] == ["--sources-only"]:
        run_skill_mirror_check()
        run_source_check()
        run_workflow_check()
        run_structure_check()
        return 0

    if argv:
        run_app(argv[0], argv[1:])
        return 0

    run_skill_mirror_check()
    run_source_check()
    run_workflow_check()
    run_structure_check()
    for root in APP_ROOTS:
        for entry in sorted((REPO_ROOT / root).iterdir()):
            if (entry / "scripts" / "check.py").is_file():
                run_app(entry.name, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
