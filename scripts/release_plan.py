#!/usr/bin/env python3
"""增量发版的计划脚本（ADR 0171）。

prepare、readiness 和 CI 共用这一份判断，避免两套口径：

- ``plan`` 在本地算「谁有改动、该升到哪」。依赖图只在这里算。
- ``matrix`` 不算依赖图，只比较两个 ref 上清单里的版本号。CI 用这个结果展开矩阵，
  重发 tag 时结果稳定。

写版本进清单是 T-008 的事。这里的写入函数只给自测和后续 prepare 调用，
``plan`` / ``matrix`` 本身不写文件、不改 git 状态。

pnpm 的 ``--filter "...[ref]"`` 语义是「自 ref 以来改过的包，以及依赖它们的包」。
这里用工作区 ``package.json`` 里的 ``workspace:`` 依赖做同一件事：锁文件一变就全量
行不通（ADR 0171 的取舍），而且不必为了计划去安装依赖。Rust 侧按任务书走
``cargo metadata`` 的工作区依赖。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPS_FILE = Path(__file__).resolve().parent / "release_apps.json"

# 与 release.yml 里 tauri-apps 矩阵的四个平台逐字相同。顺序即 CI 展开顺序。
TAURI_PLATFORMS = (
    {"os": "windows-latest", "platform": "windows-x64", "bundles": "nsis"},
    {"os": "macos-15", "platform": "macos-arm64", "bundles": "app,dmg"},
    {"os": "macos-15-intel", "platform": "macos-x86_64", "bundles": "app,dmg"},
    {"os": "ubuntu-26.04", "platform": "linux-x86_64", "bundles": "deb"},
)

# 这些树的改动不代表任何一个应用要重新构建。`.github/` 整树也不按路径算，
# 工具链版本另走 release.yml 里的锁定值比较。
IGNORED_PREFIXES = ("comms/", "docs/", "scripts/", ".github/")

# prepare 与回填会改写各应用清单里的版本行。清单文件只有版本行不同，不能当成应用自己
# 有改动，否则每次发版都自激（回填提交曾让 26 个应用全部显示「有改动」）。
VERSION_LINE_RE = re.compile(
    r"""^\s*("version"\s*:\s*"[^"]*"|version:\s*'[^']*'|version:\s*[^\s']+)\s*,?\s*$"""
)

# v10.0.0 及更早的发版是全量构建、所有应用同一个版本号，清单里没有应用自己的版本
# （占位 0.1.0）。这些 tag 上，应用的有效版本就是 tag 版本（ADR 0171）。
LEGACY_LAST = (10, 0, 0)
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

JSON_VERSION_RE = re.compile(r'("version"\s*:\s*")([^"]*)(")')
PUBSPEC_VERSION_RE = re.compile(r"^(version:\s*)(\d+\.\d+\.\d+)(\+[^\s]+)?", re.MULTILINE)
MESON_VERSION_RE = re.compile(r"(version:\s*')([^']*)(')")

FEAT_RE = re.compile(r"(^|\s)feat(\(|!|:)", re.IGNORECASE)
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\+.+)?$")

# matrix 里这四项是布尔，不进 tauri.include。ascent 虽是 Tauri 壳，但有自己的更新器作业。
BOOL_IDS = ("cpp", "driver", "ascent", "c-gui-lab")


def force_utf8_output() -> None:
    """中文 Windows 控制台默认不是 UTF-8。与 release.py readiness 同一做法。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_apps(path: Path | None = None) -> list[dict]:
    file = path or APPS_FILE
    apps = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(apps, list) or not apps:
        raise SystemExit(f"{file} 不是应用清单")
    return apps


def app_dir(app: dict) -> str:
    return f"{app['root']}/{app['id']}"


def read_version(data: bytes, manifest_format: str) -> str:
    text = data.decode("utf-8")
    if manifest_format in ("tauri_conf", "package_json"):
        match = JSON_VERSION_RE.search(text)
    elif manifest_format == "pubspec":
        match = PUBSPEC_VERSION_RE.search(text)
    elif manifest_format == "meson":
        match = MESON_VERSION_RE.search(text)
    else:
        raise ValueError(f"未知清单格式 {manifest_format}")
    if match is None:
        raise ValueError(f"清单里没有版本字段（{manifest_format}）")
    if manifest_format == "pubspec":
        return match.group(2) + (match.group(3) or "")
    return match.group(2)


def write_version(data: bytes, manifest_format: str, new_version: str) -> bytes:
    """只替换版本那一处，其余字节原样保留。

    pubspec 的 ``+构建号`` 在新版本没写构建号时沿用，不自增。
    不用 JSON/YAML 库重写：键序、空格和换行一变，diff 就不再只是版本。
    """
    text = data.decode("utf-8")
    if manifest_format in ("tauri_conf", "package_json"):
        core = new_version.split("+", 1)[0]
        new_text, count = JSON_VERSION_RE.subn(lambda m: m.group(1) + core + m.group(3), text, count=1)
    elif manifest_format == "pubspec":
        def repl(match: re.Match[str]) -> str:
            build = match.group(3) or ""
            if "+" in new_version:
                core, extra = new_version.split("+", 1)
                build = "+" + extra
            else:
                core = new_version
            return match.group(1) + core + build

        new_text, count = PUBSPEC_VERSION_RE.subn(repl, text, count=1)
    elif manifest_format == "meson":
        core = new_version.split("+", 1)[0]
        new_text, count = MESON_VERSION_RE.subn(lambda m: m.group(1) + core + m.group(3), text, count=1)
    else:
        raise ValueError(f"未知清单格式 {manifest_format}")
    if count != 1:
        raise ValueError(f"清单里没有可替换的版本字段（{manifest_format}）")
    return new_text.encode("utf-8")


def bump_level(subjects: list[str]) -> str:
    """有改动才调用。⚠️ 或标题里的 ``!:`` 升主版本，feat 升次版本，其余升修订号。取最高的一档。"""
    level = "patch"
    for subject in subjects:
        if "⚠️" in subject or "!:" in subject:
            return "major"
        if FEAT_RE.search(subject):
            level = "minor"
    return level


def apply_bump(version: str, level: str) -> str:
    if level == "none":
        return version
    match = SEMVER_RE.match(version)
    if match is None:
        raise ValueError(f"无法解析版本 {version}")
    major, minor, patch = (int(match.group(i)) for i in (1, 2, 3))
    build = ""
    if "+" in version:
        build = "+" + version.split("+", 1)[1]
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    elif level == "patch":
        patch += 1
    else:
        raise ValueError(f"未知升级档 {level}")
    return f"{major}.{minor}.{patch}{build}"


def is_ignored_path(path: str) -> bool:
    return path.startswith(IGNORED_PREFIXES)


def version_line_only(patch: str) -> bool:
    """unified diff 里增删的行是否全是版本行（JSON、pubspec、meson 三种写法）。没有增删不算「只改了版本」。"""
    bodies: list[str] = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---", "@@", "diff ", "index ", "new file", "deleted file")):
            continue
        if line[:1] in "+-":
            bodies.append(line[1:])
    if not bodies:
        return False
    return all(VERSION_LINE_RE.match(body) for body in bodies)


def significant_paths(paths: list[str], version_only: frozenset[str] | set[str] = frozenset()) -> list[str]:
    """去掉忽略树下的文件，以及「只有版本行不同」的清单文件（version_only 由调用方逐个比出来）。"""
    return [path for path in paths if not is_ignored_path(path) and path not in version_only]


def core_version(version: str | None) -> str | None:
    """去掉 pubspec 的 +构建号再比较：构建号单独变化不算版本变化。"""
    return None if version is None else version.split("+", 1)[0]


def parse_tag(ref: str) -> tuple[int, int, int] | None:
    match = TAG_RE.match(ref)
    return None if match is None else (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def base_version(app: dict, ref: str, manifest_version) -> str | None:
    """应用在 base 上的有效版本；None 表示 base 之前没发布过（新应用）。

    legacy tag（≤ 10.0.0）上清单版本是占位，有效版本取 tag 版本，且只对当时已发布的应用
    （release_apps.json 的 first_release 不晚于该 tag）成立。更晚的 ref 直接读清单。
    """
    tag = parse_tag(ref)
    if tag is not None and tag <= LEGACY_LAST:
        first = app.get("first_release")
        if first is None:
            return None
        first_tuple = parse_tag("v" + first)
        if first_tuple is None or first_tuple > tag:
            return None
        return ".".join(str(part) for part in tag)
    return manifest_version(app)


def version_only_manifests(apps: list[dict], files: list[str], patch_of) -> set[str]:
    """改动文件里，只有版本行不同的应用清单（c-gui-lab 的 package-lock.json 同理）。"""
    candidates: dict[str, None] = {}
    for app in apps:
        manifest = app["manifest"]
        candidates[manifest] = None
        if app["manifest_format"] == "package_json":
            candidates[manifest.rsplit("/", 1)[0] + "/package-lock.json"] = None
    return {path for path in files if path in candidates and version_line_only(patch_of(path))}


def toolchain_pins(release_yml: str) -> dict[str, frozenset[str]]:
    """只认 release.yml 里锁定的 Node、pnpm、Tauri CLI。改文件的其它内容不算。

    比较的是版本值的集合，不是出现次数：同一个 ``22`` 多抄进一个作业，版本没变。
    没有锁定 Tauri CLI 时集合为空，两边都空就不触发。
    """
    node: set[str] = set()
    pnpm: set[str] = set()
    tauri: set[str] = set()
    lines = release_yml.splitlines()
    for index, line in enumerate(lines):
        node_match = re.search(r"node-version:\s*['\"]?([^'\"\s#]+)", line)
        if node_match:
            node.add(node_match.group(1))
        if "pnpm/action-setup" in line:
            for nxt in lines[index + 1 : index + 8]:
                if "node-version" in nxt:
                    continue
                ver = re.search(r"version:\s*['\"]?([^'\"\s#]+)", nxt)
                if ver:
                    pnpm.add(ver.group(1))
                    break
        for pattern in (
            r"@tauri-apps/cli@([^\s'\"#]+)",
            r"@tauri-apps/cli['\"]?\s*[:=]\s*['\"]?([^'\"\s#]+)",
        ):
            found = re.search(pattern, line)
            if found:
                tauri.add(found.group(1))
    return {"node": frozenset(node), "pnpm": frozenset(pnpm), "tauri_cli": frozenset(tauri)}


def toolchain_changed(base_text: str | None, head_text: str | None) -> bool:
    if base_text is None or head_text is None:
        return False
    return toolchain_pins(base_text) != toolchain_pins(head_text)


def _under(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory + "/")


def _closure(seeds: set[str], dependents_of: dict[str, list[str]]) -> set[str]:
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        current = stack.pop()
        for dep in dependents_of.get(current, ()):
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return seen


def _reverse(dir_to_deps: dict[str, list[str]]) -> dict[str, list[str]]:
    rev: dict[str, list[str]] = defaultdict(list)
    for directory, deps in dir_to_deps.items():
        for dep in deps:
            rev[dep].append(directory)
    return rev


def seeds_reaching(start: str, seeds: set[str], dir_to_deps: dict[str, list[str]]) -> list[str]:
    """start 依赖到的、这次确实改过的包目录。"""
    found: list[str] = []
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        for dep in dir_to_deps.get(current, ()):
            if dep in seen:
                continue
            seen.add(dep)
            if dep in seeds:
                found.append(dep)
            stack.append(dep)
    return found


def workspace_package_dirs(repo: Path) -> list[str]:
    text = (repo / "pnpm-workspace.yaml").read_text(encoding="utf-8")
    globs: list[str] = []
    in_packages = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("packages:"):
            in_packages = True
            continue
        if not in_packages:
            continue
        if stripped.startswith("#"):
            continue
        if not line.startswith((" ", "\t", "-")):
            break
        match = re.search(r'"([^"]+)"', line)
        if match:
            globs.append(match.group(1))
    dirs: list[str] = []
    for pattern in globs:
        if any(ch in pattern for ch in "*?["):
            matches = [p for p in repo.glob(pattern) if p.is_dir()]
        else:
            candidate = repo / pattern
            matches = [candidate] if candidate.is_dir() else []
        for path in matches:
            if (path / "package.json").is_file():
                dirs.append(path.relative_to(repo).as_posix())
    return sorted(set(dirs))


def pnpm_dependency_graph(repo: Path) -> dict[str, list[str]]:
    """目录 → 它用 workspace: 协议依赖的目录。等价于 pnpm filter 的下游关系，不跑安装。"""
    directories = workspace_package_dirs(repo)
    name_to_dir: dict[str, str] = {}
    parsed: dict[str, dict] = {}
    for directory in directories:
        data = json.loads((repo / directory / "package.json").read_text(encoding="utf-8"))
        parsed[directory] = data
        name = data.get("name")
        if isinstance(name, str):
            name_to_dir[name] = directory
    graph: dict[str, list[str]] = {}
    for directory, data in parsed.items():
        deps: list[str] = []
        for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            block = data.get(section) or {}
            if not isinstance(block, dict):
                continue
            for name, spec in block.items():
                if isinstance(spec, str) and spec.startswith("workspace:") and name in name_to_dir:
                    deps.append(name_to_dir[name])
        graph[directory] = deps
    return graph


def cargo_dependency_graph(metadata: dict, repo: Path) -> dict[str, list[str]]:
    """crate 目录 → 它 path 依赖的工作区 crate 目录。只保留 workspace 成员之间的边。"""
    members = set(metadata.get("workspace_members") or [])
    repo_resolved = repo.resolve()
    id_to_dir: dict[str, str] = {}
    packages = []
    for package in metadata.get("packages") or []:
        if package.get("id") not in members:
            continue
        manifest = Path(package["manifest_path"]).resolve()
        try:
            directory = manifest.parent.relative_to(repo_resolved).as_posix()
        except ValueError:
            continue
        id_to_dir[package["id"]] = directory
        packages.append(package)
    dir_set = set(id_to_dir.values())
    graph: dict[str, list[str]] = {directory: [] for directory in dir_set}
    for package in packages:
        manifest = Path(package["manifest_path"]).resolve()
        source = id_to_dir[package["id"]]
        for dep in package.get("dependencies") or []:
            raw = dep.get("path")
            if not raw:
                continue
            dep_path = Path(raw)
            if not dep_path.is_absolute():
                dep_path = (manifest.parent / dep_path).resolve()
            else:
                dep_path = dep_path.resolve()
            try:
                directory = dep_path.relative_to(repo_resolved).as_posix()
            except ValueError:
                continue
            if directory in dir_set and directory not in graph[source]:
                graph[source].append(directory)
    return graph


def _app_by_dir(apps: list[dict]) -> dict[str, dict]:
    return {app_dir(app): app for app in apps}


def _match_app(directory: str, by_dir: dict[str, dict]) -> dict | None:
    if directory.endswith("/src-tauri"):
        directory = directory[: -len("/src-tauri")]
    return by_dir.get(directory)


def decide(
    apps: list[dict],
    files: list[str],
    pnpm_graph: dict[str, list[str]],
    cargo_graph: dict[str, list[str]],
    pins_changed: bool,
    version_of,
    subjects_for,
    base_version_of=None,
) -> list[dict]:
    by_dir = _app_by_dir(apps)
    pnpm_seeds = {directory for directory in pnpm_graph if any(_under(path, directory) for path in files)}
    cargo_seeds = {directory for directory in cargo_graph if any(_under(path, directory) for path in files)}
    pnpm_hit = _closure(pnpm_seeds, _reverse(pnpm_graph))
    cargo_hit = _closure(cargo_seeds, _reverse(cargo_graph))

    decisions: list[dict] = []
    for app in apps:
        directory = app_dir(app)
        own = [path for path in files if _under(path, directory)]
        pnpm_deps = [d for d in seeds_reaching(directory, pnpm_seeds, pnpm_graph) if d != directory]
        cargo_dir = directory + "/src-tauri"
        cargo_deps = []
        if cargo_dir in cargo_graph or any(_under(s, cargo_dir) or s == cargo_dir for s in cargo_seeds):
            cargo_deps = [d for d in seeds_reaching(cargo_dir, cargo_seeds, cargo_graph) if not _under(d, directory)]
        via_pnpm = directory in pnpm_hit and not own and bool(pnpm_deps)
        via_cargo = (cargo_dir in cargo_hit or directory in cargo_hit) and not own and bool(cargo_deps)
        via_pins = pins_changed and app["kind"] in ("tauri", "ascent")
        changed = bool(own) or via_pnpm or via_cargo or via_pins
        reasons: list[str] = []
        if own:
            shown = ", ".join(own[:4])
            extra = f" 等 {len(own)} 个" if len(own) > 4 else ""
            reasons.append(f"目录有改动：{shown}{extra}")
        if pnpm_deps and (own or via_pnpm):
            reasons.append("pnpm 依赖变了：" + ", ".join(sorted(set(pnpm_deps))))
        if cargo_deps and (own or via_cargo):
            reasons.append("Rust 依赖变了：" + ", ".join(sorted(set(cargo_deps))))
        if via_pins:
            reasons.append("工具链版本变了（release.yml 里的 Node / pnpm / Tauri CLI）")
        current = version_of(app)
        base_ver = base_version_of(app) if base_version_of is not None else current
        is_new = base_version_of is not None and base_ver is None
        already = (
            not is_new
            and current is not None
            and base_ver is not None
            and core_version(current) != core_version(base_ver)
        )
        if is_new:
            changed = True
            reasons.append("新应用：base 之前没有发布过，版本保持清单里的值，不升")
        elif already and changed:
            reasons.append(f"清单版本已是 {current}（base 有效版本 {base_ver}），视为已升，不再建议")
        commits: list[str] = []
        suggested = current
        level = "none"
        if changed and not is_new and not already:
            pathspecs = [directory]
            pathspecs.extend(pnpm_deps)
            pathspecs.extend(cargo_deps)
            if via_pins:
                pathspecs.append(".github/workflows/release.yml")
            commits = subjects_for(pathspecs)
            level = bump_level(commits)
            if current is None:
                suggested = None
                reasons.append("HEAD 上没有清单版本，无法给出建议版本")
            else:
                suggested = apply_bump(current, level)
        decisions.append(
            {
                "id": app["id"],
                "kind": app["kind"],
                "root": app["root"],
                "changed": changed,
                "current": current,
                "suggested": suggested,
                "bump": level,
                "reasons": reasons,
                "commits": commits,
                "new": is_new,
            }
        )
    return decisions


def format_plan_text(base: str, head: str, decisions: list[dict]) -> str:
    changed = [item for item in decisions if item["changed"]]
    lines = [f"base {base}  head {head}", f"有改动 {len(changed)} / 共 {len(decisions)}", ""]
    for item in changed:
        if item.get("new"):
            lines.append(f"{item['id']}\t{item['current'] or '—'}（新应用）")
        else:
            lines.append(
                f"{item['id']}\t{item['current'] or '—'} → {item['suggested'] or '—'} ({item['bump']})"
            )
        for reason in item["reasons"]:
            lines.append(f"  {reason}")
        if item["commits"]:
            shown = item["commits"][:6]
            lines.append("  提交：" + "；".join(shown))
            if len(item["commits"]) > len(shown):
                lines.append(f"  … 另有 {len(item['commits']) - len(shown)} 条提交")
        lines.append("")
    unchanged = [item["id"] for item in decisions if not item["changed"]]
    lines.append("未改动：" + ("、".join(unchanged) if unchanged else "（无）"))
    return "\n".join(lines).rstrip() + "\n"


def format_plan_json(base: str, head: str, decisions: list[dict]) -> str:
    payload = {"base": base, "head": head, "apps": decisions}
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def matrix_from_versions(apps: list[dict], base_versions: dict[str, str | None], head_versions: dict[str, str | None]) -> dict:
    """版本字符串不同，或 base 上还没有这份清单，就算这次要构建。两边都没有则跳过。"""
    include: list[dict] = []
    flags = {key: False for key in BOOL_IDS}
    for app in apps:
        base = base_versions.get(app["id"])
        head = head_versions.get(app["id"])
        if head is None and base is None:
            continue
        if base is not None and head is not None and core_version(base) == core_version(head):
            continue
        if app["kind"] == "tauri":
            for platform in TAURI_PLATFORMS:
                include.append({"app": app["id"], "root": app["root"], **platform})
        elif app["id"] in flags:
            flags[app["id"]] = True
    return {"tauri": {"include": include}, **flags}


def format_matrix(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(", ", ": ")) + "\n"


def _git(repo: Path, args: list[str], *, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise SystemExit(f"git {' '.join(args)} 失败：{detail}")
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8", "replace")


def latest_version_tag(repo: Path) -> str:
    text = _git(repo, ["tag", "-l", "v[0-9]*.[0-9]*.[0-9]*", "--sort=-v:refname"])
    assert isinstance(text, str)
    for line in text.splitlines():
        if re.fullmatch(r"v\d+\.\d+\.\d+", line.strip()):
            return line.strip()
    raise SystemExit("找不到 vX.Y.Z 形式的 tag，请用 --base 指定")


def changed_files(repo: Path, base: str, head: str) -> list[str]:
    raw = _git(repo, ["diff", "--name-only", "-z", base, head], binary=True)
    assert isinstance(raw, bytes)
    return [part.decode("utf-8") for part in raw.split(b"\0") if part]


def file_at(repo: Path, ref: str, path: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def version_at(repo: Path, ref: str, app: dict) -> str | None:
    data = file_at(repo, ref, app["manifest"])
    if data is None:
        return None
    return read_version(data, app["manifest_format"])


def commit_subjects(repo: Path, base: str, head: str, paths: list[str]) -> list[str]:
    if not paths:
        return []
    text = _git(repo, ["log", f"{base}..{head}", "--format=%s", "--", *paths])
    assert isinstance(text, str)
    return [line for line in text.splitlines() if line.strip()]


def load_cargo_metadata(repo: Path) -> dict:
    completed = subprocess.run(
        ["cargo", "metadata", "--format-version", "1", "--no-deps"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise SystemExit(f"cargo metadata 失败：{detail}")
    return json.loads(completed.stdout.decode("utf-8"))


def compute_decisions(repo: Path, apps: list[dict], base: str, head: str) -> list[dict]:
    """plan 的核心：每个应用一条决定。prepare、readiness 直接调用这个，不经文本输出。"""
    files = changed_files(repo, base, head)

    def patch_of(path: str) -> str:
        diff = _git(repo, ["diff", base, head, "--", path])
        assert isinstance(diff, str)
        return diff

    files = significant_paths(files, version_only_manifests(apps, files, patch_of))
    base_yml = file_at(repo, base, ".github/workflows/release.yml")
    head_yml = file_at(repo, head, ".github/workflows/release.yml")
    pins_changed = toolchain_changed(
        None if base_yml is None else base_yml.decode("utf-8", "replace"),
        None if head_yml is None else head_yml.decode("utf-8", "replace"),
    )
    decisions = decide(
        apps,
        files,
        pnpm_dependency_graph(repo),
        cargo_dependency_graph(load_cargo_metadata(repo), repo),
        pins_changed,
        lambda app: version_at(repo, head, app),
        lambda paths: commit_subjects(repo, base, head, paths),
        lambda app: base_version(app, base, lambda a: version_at(repo, base, a)),
    )
    return decisions


def run_plan(repo: Path, apps: list[dict], base: str, head: str, as_json: bool) -> str:
    decisions = compute_decisions(repo, apps, base, head)
    if as_json:
        return format_plan_json(base, head, decisions)
    return format_plan_text(base, head, decisions)


def build_notes(apps: list[dict], tags: list[str], base_ver, head_ver, tag_ver) -> str:
    """发布说明里的两张表（ADR 0171）：本次发布的应用，与没变的应用最新装在哪一版。

    base_ver/head_ver：应用在 base（上一个 tag）与本次的有效版本；tag_ver(app, tag)：应用在某个
    tag 的有效版本。没变的应用，它当前版本最早出现的 tag 就是它最新安装包所在的发布。
    """
    released: list[tuple[str, str]] = []
    unchanged: list[tuple[str, str, str]] = []
    for app in apps:
        head = head_ver(app)
        if head is None:
            continue
        base = base_ver(app)
        if base is None:
            released.append((app["id"], f"首发 {head}"))
        elif core_version(base) != core_version(head):
            released.append((app["id"], f"{core_version(base)} → {core_version(head)}"))
        else:
            where = next((tag for tag in tags if core_version(tag_ver(app, tag)) == core_version(head)), "—")
            unchanged.append((app["id"], core_version(head) or "—", where))
    lines = ["### 本次发布的应用", "", "| 应用 | 版本 |", "|---|---|"]
    lines += [f"| {name} | {text} |" for name, text in released] or ["| （无） | |"]
    lines += ["", "### 未变化的应用", "", "没动过的应用不进本次 Release，最新安装包在它标注的那一版里。", ""]
    lines += ["| 应用 | 当前版本 | 最新安装包 |", "|---|---|---|"]
    lines += [f"| {name} | {version} | {tag} |" for name, version, tag in unchanged] or ["| （无） | | |"]
    return "\n".join(lines) + "\n"


def version_tags(repo: Path, upto: str, limit: int = 30) -> list[str]:
    """升序的 vX.Y.Z tag，截止到 upto（含）；只取最近 limit 个，够找「当前版本最早出现在哪」。"""
    text = _git(repo, ["tag", "-l", "v[0-9]*.[0-9]*.[0-9]*", "--sort=v:refname"])
    assert isinstance(text, str)
    tags = [line.strip() for line in text.splitlines() if TAG_RE.match(line.strip())]
    limit_tuple = parse_tag(upto)
    if limit_tuple is not None:
        tags = [tag for tag in tags if parse_tag(tag) <= limit_tuple]
    return tags[-limit:]


def run_notes(repo: Path, apps: list[dict], base: str, head: str) -> str:
    tags = version_tags(repo, base)
    return build_notes(
        apps,
        tags,
        lambda app: base_version(app, base, lambda a: version_at(repo, base, a)),
        lambda app: version_at(repo, head, app),
        lambda app, tag: base_version(app, tag, lambda a: version_at(repo, tag, a)),
    )


def run_matrix(repo: Path, apps: list[dict], base: str, head: str) -> str:
    base_versions = {app["id"]: base_version(app, base, lambda a: version_at(repo, base, a)) for app in apps}
    head_versions = {app["id"]: version_at(repo, head, app) for app in apps}
    return format_matrix(matrix_from_versions(apps, base_versions, head_versions))


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="增量发版计划（ADR 0171）")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    parser.add_argument("--apps", type=Path, default=APPS_FILE)
    sub = parser.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan", help="算改动集与建议版本")
    plan.add_argument("--base", help="比较起点，默认最近的 vX.Y.Z tag")
    plan.add_argument("--head", default="HEAD")
    plan.add_argument("--json", action="store_true")

    matrix = sub.add_parser("matrix", help="按清单版本差输出 CI 矩阵")
    matrix.add_argument("--base", required=True)
    matrix.add_argument("--head", required=True)

    notes = sub.add_parser("notes", help="发布说明里的两张表：本次发布的应用、未变化应用的最新安装包在哪一版")
    notes.add_argument("--base", required=True)
    notes.add_argument("--head", required=True)

    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    apps = load_apps(args.apps)
    if args.cmd == "plan":
        base = args.base or latest_version_tag(repo)
        sys.stdout.write(run_plan(repo, apps, base, args.head, args.json))
    elif args.cmd == "notes":
        sys.stdout.write(run_notes(repo, apps, args.base, args.head))
    else:
        sys.stdout.write(run_matrix(repo, apps, args.base, args.head))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
