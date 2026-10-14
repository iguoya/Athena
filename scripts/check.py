#!/usr/bin/env python3
"""仓库统一验证入口（ADR 0007、0045、0047）。

检查逻辑归各应用自己（各应用根目录 APP_ROOTS 下的 scripts/check.py），
这里只负责依次调用，
外加四项跨应用检查：内容必须有出处（ADR 0043），项目 skill 在 .agents/ 与
.claude/ 两处一致（ADR 0061），GitHub 工作流过 actionlint 与变量粘连检查，
同栈应用核心依赖版本一致（ADR 0135），结构卫生（文档树对账、应用四件套、ADR 索引覆盖）。新增应用放一份自己的
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
# 课程类学习应用按分组分目录（ADR 0150），其余按应用类别分；增减分组目录只改这两行。
GROUP_ROOTS = ("programming", "artificial-intelligence", "computer-fundamentals", "electronics", "postgraduate")
APP_ROOTS = (*GROUP_ROOTS, "guide", "practice", "certification", "mentor", "tools")
_ROOTS_RE = "|".join(APP_ROOTS)


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
    app_dir = find_app(app)
    entry = app_dir / "scripts" / "check.py"
    if not entry.is_file():
        raise SystemExit(f"应用 {app} 没有 {entry.relative_to(REPO_ROOT)}")
    # 工作区成员的依赖装在仓库根（ADR 0140）。应用自己的检查只在 node_modules
    # 还不存在时才会再装；这里先装好，避免它因找不到本目录的锁文件而裸装。
    rel = app_dir.relative_to(REPO_ROOT).as_posix()
    in_workspace = rel.startswith(tuple(f"{root}/" for root in APP_ROOTS if root != "practice")) or rel == "practice/earth"
    if in_workspace and (app_dir / "package.json").is_file() and not (app_dir / "node_modules").is_dir():
        if not (REPO_ROOT / "pnpm-lock.yaml").is_file():
            raise SystemExit("仓库根没有 pnpm-lock.yaml，先在仓库根执行 pnpm install（ADR 0140）")
        print("== 安装工作区前端依赖 ==", flush=True)
        completed = subprocess.run(["pnpm", "install", "--frozen-lockfile"], cwd=REPO_ROOT)
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)
    print(f"== 检查应用：{app} ==", flush=True)
    completed = subprocess.run([sys.executable, str(entry), *extra], cwd=app_dir)
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


# 同栈核心依赖的版本范围。真正的声明在 pnpm-workspace.yaml 的 catalog（ADR 0140），
# 这里留一份是为了检查两边没有漂。升级时两处一起改。不跳到尚无应用验证过的大版本
# （如 TypeScript 7）。表里没列的依赖不管。
STACK_VERSIONS = {
    "react": "^19.3.0", "react-dom": "^19.3.0",
    "@types/react": "^19.3.0", "@types/react-dom": "^19.3.0",
    "@vitejs/plugin-react": "^6.1.1",
    "vite": "^8.3.1", "typescript": "^6.0.3",
    "tailwindcss": "^4.3.3", "@tailwindcss/vite": "^4.3.3",
    "@tauri-apps/api": "^2.12.0", "@tauri-apps/cli": "^2.12.0",
    "@tauri-apps/plugin-opener": "^2.7.0",
    "@fontsource/noto-sans-sc": "^5.3.0",
    "lucide-react": "^1.52.0", "motion": "^14.0.0",
    "three": "^0.182.0", "@types/three": "^0.182.0",
    "@react-three/fiber": "^9.6.0", "@react-three/drei": "^10.7.9",
}
PNPM_PIN = "pnpm@10.15.1"
# 例外必须写理由：(应用, 依赖) -> 为什么不跟。"*" 表示该应用整体豁免。
STACK_VERSION_EXEMPT: dict[tuple[str, str], str] = {}


def load_pnpm_catalog() -> dict[str, str]:
    catalog: dict[str, str] = {}
    in_catalog = False
    for line in (REPO_ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("catalog:"):
            in_catalog = True
            continue
        if not in_catalog:
            continue
        if line and not line.startswith((" ", "#")):
            break
        match = re.match(r"\s{2}(\S+):\s+(\S+)\s*$", line)
        if match:
            catalog[match.group(1).strip('"')] = match.group(2)
    return catalog


def workspace_dependencies_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\[workspace\.dependencies\]\n(.*?)(?:\n\[|\Z)", text, re.S)
    return match.group(1).strip() if match else ""


def run_stack_version_check() -> None:
    """同栈应用的核心依赖必须走同一份 catalog（ADR 0135、0140）。"""
    import json

    print("== 跨应用检查：同栈核心依赖版本 ==", flush=True)
    problems: list[str] = []
    if not (REPO_ROOT / "pnpm-workspace.yaml").is_file():
        problems.append("  仓库根缺 pnpm-workspace.yaml（ADR 0140）")
    else:
        catalog = load_pnpm_catalog()
        if catalog != STACK_VERSIONS:
            problems.append("  pnpm-workspace.yaml 的 catalog 与 STACK_VERSIONS 不一致（ADR 0140）")
    if not (REPO_ROOT / "pnpm-lock.yaml").is_file():
        problems.append("  仓库根缺 pnpm-lock.yaml，在仓库根执行 pnpm install 后提交（ADR 0140）")

    frontends: list[tuple[str, Path]] = []
    for root in APP_ROOTS:
        for app in sorted((REPO_ROOT / root).iterdir()):
            if (app / "package.json").is_file() and (app / "src-tauri" / "Cargo.toml").is_file():
                frontends.append((f"{root}/{app.name}", app))
    launcher_webui = REPO_ROOT / "launcher" / "webui"
    if (launcher_webui / "package.json").is_file():
        frontends.append(("launcher/webui", launcher_webui))

    for label, app in frontends:
        pkg = app / "package.json"
        data = json.loads(pkg.read_text(encoding="utf-8"))
        if (app / "package-lock.json").exists():
            problems.append(f"  {label} 还有 package-lock.json（ADR 0136）")
        if (app / "pnpm-lock.yaml").exists():
            problems.append(f"  {label} 还有自己的 pnpm-lock.yaml，锁文件只留仓库根一份（ADR 0140）")
        if data.get("packageManager") != PNPM_PIN:
            problems.append(f"  {label} 的 packageManager 是 {data.get('packageManager')!r}，应为 {PNPM_PIN}")
        declared = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        for name in STACK_VERSIONS:
            have = declared.get(name)
            if have is None or (app.name, name) in STACK_VERSION_EXEMPT or (app.name, "*") in STACK_VERSION_EXEMPT:
                continue
            if have != "catalog:":
                problems.append(f"  {label} 的 {name} 是 {have}，应为 catalog:（ADR 0140）")
    if problems:
        print("\n".join(problems), flush=True)
        raise SystemExit(f"同栈依赖版本不一致（{len(problems)} 处）。")


def run_shared_build_check() -> None:
    """同栈 Rust 共用一个编译目录，两份工作区的依赖表必须相同（ADR 0140）。"""
    print("== 跨应用检查：共用编译目录与 Cargo 工作区 ==", flush=True)
    problems: list[str] = []
    config = REPO_ROOT / ".cargo" / "config.toml"
    if not config.is_file() or ".cache/cargo-target" not in config.read_text(encoding="utf-8"):
        problems.append("  .cargo/config.toml 没有把 target-dir 指到 .cache/cargo-target")
    root_block = workspace_dependencies_block(REPO_ROOT / "Cargo.toml")
    launcher_block = workspace_dependencies_block(REPO_ROOT / "launcher" / "Cargo.toml")
    if not root_block or root_block != launcher_block:
        problems.append("  仓库根与 launcher/Cargo.toml 的 workspace.dependencies 不一致")
    if not (REPO_ROOT / "Cargo.lock").is_file():
        problems.append("  仓库根缺 Cargo.lock，在仓库根执行 cargo generate-lockfile 后提交")
    declared = set(re.findall(r'"((?:' + _ROOTS_RE + r')/[^"]+/src-tauri)"', (REPO_ROOT / "Cargo.toml").read_text(encoding="utf-8")))
    found = {
        path.parent.relative_to(REPO_ROOT).as_posix()
        for root in APP_ROOTS if root != "practice"
        for path in (REPO_ROOT / root).glob("*/src-tauri/Cargo.toml")
    }
    earth = REPO_ROOT / "practice" / "earth" / "src-tauri" / "Cargo.toml"
    if earth.is_file():
        found.add("practice/earth/src-tauri")
    if declared != found:
        missing = ", ".join(sorted(found - declared)) or "无"
        extra = ", ".join(sorted(declared - found)) or "无"
        problems.append(f"  根 Cargo.toml 成员与实际 src-tauri 不一致。缺：{missing}。多：{extra}")
    for rel in sorted(found):
        lock = REPO_ROOT / rel / "Cargo.lock"
        if lock.is_file():
            problems.append(f"  {rel}/Cargo.lock 应删除，锁文件只留仓库根（ADR 0140）")
    if problems:
        print("\n".join(problems), flush=True)
        raise SystemExit(f"共用构建检查没通过（{len(problems)} 处）。")


# 课程/讲解/演示类应用统一 Tauri 2 + React（ADR 0138 决策 2、9）。
# 豁免表逐项列出尚未迁移或本轮暂缓的应用，**每迁完一个就删一行**，表空即全部统一。
# 这里只管课程类分组目录、mentor/ 与 tools/（学习应用、图谱/参考类、配套工具）；practice/ 自由发挥，不检查。
REACT_FRONTEND_EXEMPT: dict[str, str] = {
    "algorithms": "原生 TS 同源壳，待 ADR 0138 迁移（波 4）",
    "cs408": "原生 TS 同源壳，待 ADR 0138 迁移（波 4）",
    "data-structures": "原生 TS 同源壳，待 ADR 0138 迁移（波 4）",
    "linux": "原生 TS 同源壳，待 ADR 0138 迁移（波 4）",
    "organization": "原生 TS 同源壳，待 ADR 0138 迁移（波 4）",
    "design-patterns": "原生 TS 自有壳，待 ADR 0138 迁移（波 6）",
    "mathematics": "原生 TS 自有壳，待 ADR 0138 迁移（波 6）",
    "machine": "Qt6/QML 壳，待 ADR 0138 决策 7 与 machine ADR 0008 迁移（波 5）",
    "driver": "Flutter 存量投入，ADR 0138 决策 8 本轮暂缓",
}
# 正在迁移、落库前后两种状态都放行的应用。空表表示没有这种过渡。
REACT_FRONTEND_EITHER: dict[str, str] = {}


def run_react_frontend_check() -> None:
    """课程/图谱类应用必须是 Tauri 2 + React，Vue 一律不允许（ADR 0138）。"""
    import json

    print("== 跨应用检查：课程类前端统一 Tauri 2 + React ==", flush=True)
    problems: list[str] = []
    for app in sorted(p for root in APP_ROOTS if root != "practice" for p in (REPO_ROOT / root).iterdir()):
        if not (app / "app.json").is_file():
            continue
        where = f"{app.parent.name}/{app.name}"
        pkg = app / "package.json"
        tauri = pkg.is_file() and (app / "src-tauri" / "Cargo.toml").is_file()
        if app.name in REACT_FRONTEND_EITHER:
            continue
        if not tauri:
            if app.name not in REACT_FRONTEND_EXEMPT:
                problems.append(f"  {where} 不是 Tauri + Node 应用，又不在 REACT_FRONTEND_EXEMPT（ADR 0138）")
            continue
        data = json.loads(pkg.read_text(encoding="utf-8"))
        declared = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        if "vue" in declared:
            problems.append(f"  {where} 还在用 Vue，课程类前端统一 React，Vue 不允许（ADR 0138）")
        has_react = "react" in declared
        exempt = app.name in REACT_FRONTEND_EXEMPT
        if not has_react and not exempt:
            problems.append(f"  {where} 的前端不是 React，又不在 REACT_FRONTEND_EXEMPT（ADR 0138）")
        if has_react and exempt:
            problems.append(f"  {where} 已是 React，应从 REACT_FRONTEND_EXEMPT 删掉这一行")
    # 豁免名单按应用 id 对账，不限 subjects/：驾考迁到 certification/ 后仍是
    # Flutter 暂缓项（ADR 0138 决策 8、0142），不能因为离开 subjects/ 就被当成已删除。
    known = {
        p.name
        for root in APP_ROOTS
        for p in (REPO_ROOT / root).iterdir()
        if p.is_dir() and (p / "app.json").is_file()
    }
    for name in (*REACT_FRONTEND_EXEMPT, *REACT_FRONTEND_EITHER):
        if name not in known:
            problems.append(f"  REACT_FRONTEND_EXEMPT 里的 {name} 已不存在，删掉这一行")
    if problems:
        print("\n".join(problems), flush=True)
        raise SystemExit(f"课程类前端统一检查没通过（{len(problems)} 处）。")


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
_GROUP_RE = re.compile(r"^(" + _ROOTS_RE + r")/")

# 仓库根只认这些条目：文档、代理与编辑器配置、六大功能区。别的出现在根下
# 要么登记进来，要么进 .gitignore，要么删——launcher_list_out.txt、
# __pycache__、dist-driver 三次杂物全都堆在根，不是巧合，根是随手一放的地方。
_ROOT_ALLOW = {
    "AGENTS.md", "CLAUDE.md", "README.md", "CHANGELOG.md", "LICENSE",
    ".git", ".gitignore", ".gitattributes", ".zcodeignore",
    ".agents", ".claude", ".cursor", ".gemini", ".vscode", ".github",
    ".cargo", "Cargo.toml", "Cargo.lock",
    "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml",
    *APP_ROOTS, "launcher", "docs", "scripts", "archive",
    "packages",
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
    tree: dict[str, set[str]] = {root: set() for root in APP_ROOTS}
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
    for root in APP_ROOTS:
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

    # 2a. 生命周期字段（ADR 0139）：app.json 写了 lifecycle 就必须是三档枚举之一。
    #     启动器对未知值按 active 兜底、不让应用消失，这里拦在更早：档位是内容
    #     决定，写错等于归错了类——「冻结归档」被静默当成「活跃学习」正是要防的。
    import json as _json

    for root in APP_ROOTS:
        for entry in sorted((REPO_ROOT / root).iterdir()):
            manifest = entry / "app.json"
            if not manifest.is_file():
                continue
            data = _json.loads(manifest.read_text(encoding="utf-8"))
            if data.get("lifecycle", "active") not in ("active", "built", "archived"):
                problems.append(
                    f"  {root}/{entry.name} 的 lifecycle「{data.get('lifecycle')}」"
                    "只认 active / built / archived（ADR 0139）"
                )

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

    # 7. 应用清单三处对账：根 README 的应用表、REPOSITORY.md 的名字表、ci.yml 的
    #    手动选择项，逐一与实际目录核对。「新增一个应用时动哪些地方」（REPOSITORY.md
    #    第 3、4 条）最容易漏的就是这几处登记——启动器靠目录自动发现，漏登不报错，
    #    等发现时文档里早就是幽灵行或缺口了。方向抓两种：文档/工作流里点名了
    #    不存在的应用（幽灵），以及开工的应用（有 app.json）没进清单（漏登）。
    readme_refs = {
        f"{group}/{name}"
        for group, name in re.findall(r"\((" + _ROOTS_RE + r")/([\w-]+)\)", (REPO_ROOT / "README.md").read_text(encoding="utf-8"))
    }
    actual_dirs = {f"{root}/{p.name}" for root in APP_ROOTS for p in (REPO_ROOT / root).iterdir() if p.is_dir()}
    working_apps = {f"{root}/{p.name}" for root in APP_ROOTS for p in (REPO_ROOT / root).iterdir() if (p / "app.json").is_file()}
    for ghost in sorted(readme_refs - actual_dirs):
        problems.append(f"  根 README.md 应用表链接到 {ghost}，实际没有这个目录")
    for missing in sorted(working_apps - readme_refs):
        problems.append(f"  根 README.md 应用表没有登记开工应用 {missing}（加一行）")

    learning_dirs = {p.name for root in (*GROUP_ROOTS, "guide", "mentor") for p in (REPO_ROOT / root).iterdir() if p.is_dir()}
    learning_working = {p.name for root in (*GROUP_ROOTS, "guide", "mentor") for p in (REPO_ROOT / root).iterdir() if (p / "app.json").is_file()}
    app_dir_names = {
        p.name
        for root in APP_ROOTS
        for p in (REPO_ROOT / root).iterdir()
        if p.is_dir()
    }
    # 名字表的行特征是第三列进程名以 `athena-` 开头——学习者目录等别的表格第一列
    # 也有反引号词（`last`，第三列还有 `null`），只认反引号会把它们误当应用。
    name_table = set(
        re.findall(r"^\| `([\w-]+)` \|[^|]+\| `athena-", repository_doc.read_text(encoding="utf-8"), re.MULTILINE)
    )
    for ghost in sorted(name_table - app_dir_names):
        problems.append(f"  docs/REPOSITORY.md 名字表写了 {ghost}，应用目录里没有这个目录")
    for missing in sorted(learning_working - name_table):
        problems.append(f"  docs/REPOSITORY.md 名字表没有登记开工应用 {missing}")

    # all / sources 是伪应用，launcher 是启动器自身的矩阵位，都不是应用目录
    for ghost in sorted(ci_apps - {"all", "sources", "launcher"} - app_dir_names):
        problems.append(f"  ci.yml 手动选择项 {ghost} 不是实际存在的应用目录")

    # 8. 应用区不留影子目录：各应用根目录与 launcher/ 下不允许「未跟踪也未
    #    忽略」的目录。应用改 id 或退役后，磁盘上常剩下只剩构建产物的旧目录——
    #    c、cpp、dsa、english 四个旧名最多各留了 1.9 GB 的 build 与 node_modules，
    #    被忽略的对账看不见，未跟踪的等在第一次 `git add -A` 的路上。目录要么被
    #    git 跟踪，要么整个删掉，半在半不在就是结构混乱本身。
    #    `--directory` 会把「目录未跟踪、内部全被忽略」的（如 Tauri 的 gen/，只有
    #    已忽略的 schemas）也整目录列出，逐个复查内部确有未跟踪文件才算数。
    completed = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--directory", "-z",
         "--", *APP_ROOTS, "launcher"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    for entry in completed.stdout.split("\0"):
        if not entry.endswith("/"):
            continue
        inner = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "-z", "--", entry],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        if any(inner.stdout.split("\0")):
            problems.append(f"  {entry} 是未跟踪的目录——登记进 git、写进 .gitignore，或整个删掉")

    # 9. 公共呈现件防回流（ADR 0137）：packages/*/src/ 收编过的组件，应用 src/ 里
    #    不许再有同名拷贝——六份 trace-player 就是从「顺手抄一份」攒出来的，改一个
    #    bug 要改六处，还会各自漂移。新公共件入包后，同名文件即视为回流。
    package_sources = {
        p.name for p in (REPO_ROOT / "packages").glob("*/src/*") if p.is_file()
    }
    for root in APP_ROOTS:
        for app_dir in sorted((REPO_ROOT / root).iterdir()):
            src = app_dir / "src"
            if not src.is_dir():
                continue
            for ghost in sorted(package_sources & {p.name for p in src.iterdir() if p.is_file()}):
                problems.append(
                    f"  {root}/{app_dir.name}/src/{ghost} 与公共包重复——用 packages/ 里的版本，别留拷贝"
                )

    # 10. 进度库守门（ADR 0155）：学习进度本机优先、永不进 git。应用的 Rust 源码
    #     里一旦建了 learning.db，app.json 就必须声明 progress（目录名与合并规则），
    #     否则启动器不会同步它；已被 git 跟踪的 progress/*.db 一律不许有（archive/ 是历史归档）。
    #     只管 src-tauri/src：driver 有自己的通路，脚本里提到旧库不算数。
    for root in APP_ROOTS:
        for app_dir in sorted((REPO_ROOT / root).iterdir()):
            manifest = app_dir / "app.json"
            src = app_dir / "src-tauri" / "src"
            if not manifest.is_file() or not src.is_dir():
                continue
            uses_db = any("learning.db" in p.read_text(encoding="utf-8", errors="ignore") for p in src.rglob("*.rs"))
            if uses_db and "progress" not in _json.loads(manifest.read_text(encoding="utf-8")):
                problems.append(
                    f"  {root}/{app_dir.name} 的源码建了 learning.db，但 app.json 没有声明 progress（ADR 0155）"
                )
    tracked_dbs = subprocess.run(
        ["git", "ls-files", "-z", "--", *(f"{root}/*/progress/*.db" for root in APP_ROOTS)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout.split("\0")
    problems += [f"  {path} 是进度库却被 git 跟踪——进度永不进 git（ADR 0155）" for path in tracked_dbs if path]

    # 11. 「最近一次」不许按自增 id 认（ADR 0155、0160）：同步拉回的旧记录入库晚、id 更大，
    #     MAX(id) / ORDER BY id DESC 会把别的设备昨天的答错当成最近一次。这个写法在
    #     snake、chinese-chess、software、embedded 里各抄过一份、各踩过一次，壳又是各应用
    #     各写一份，没有共用代码可改——只能靠检查拦回流。要认时间，用 answered_at 再按 id。
    id_order = re.compile(r"MAX\(\s*id\s*\)|ORDER\s+BY\s+(?:\w+\.)?id\s+DESC", re.IGNORECASE)
    for root in APP_ROOTS:
        for app_dir in sorted((REPO_ROOT / root).iterdir()):
            src = app_dir / "src-tauri" / "src"
            if not src.is_dir():
                continue
            for source in sorted(src.rglob("*.rs")):
                for number, line in enumerate(source.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                    if id_order.search(line) and not line.lstrip().startswith("//"):
                        problems.append(
                            f"  {source.relative_to(REPO_ROOT)}:{number} 按自增 id 判先后——"
                            "同步拉回的旧记录 id 更大，改按 answered_at（同秒再按 id）"
                        )

    if problems:
        print("\n".join(problems), flush=True)
        raise SystemExit(f"结构卫生没通过（{len(problems)} 处），见上方。")
    print(
        f"结构树与 {sum(len(v) for v in tree.values())} 个应用目录一致，"
        f"四件套齐备，ADR 索引全覆盖，根目录干净，产物全被忽略，"
        f"发布矩阵 {len(released)} 个应用全部有 CI，"
        f"README/名字表/CI 选择项与 {len(actual_dirs)} 个目录对账一致，应用区无影子目录，公共件无回流",
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
        run_stack_version_check()
        run_shared_build_check()
        run_react_frontend_check()
        run_structure_check()
        return 0

    if argv:
        run_app(argv[0], argv[1:])
        return 0

    run_skill_mirror_check()
    run_source_check()
    run_workflow_check()
    run_stack_version_check()
    run_shared_build_check()
    run_react_frontend_check()
    run_structure_check()
    for root in APP_ROOTS:
        for entry in sorted((REPO_ROOT / root).iterdir()):
            if (entry / "scripts" / "check.py").is_file():
                run_app(entry.name, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
