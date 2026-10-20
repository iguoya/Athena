#!/usr/bin/env python3
"""发版前只读体检：把 prepare 才会拦、以及容易拖到打 tag 才发现的几处汇成一张表。

由 ``python scripts/release.py readiness`` 转调。不 fetch、不写仓库、不改 git 状态；
需要远端视图时提示使用者先 ``git fetch``。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TextIO

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
RELEASE_TODO = REPO_ROOT / "docs/RELEASE-TODO.md"
MESON_BUILD = REPO_ROOT / "practice/cpp/meson.build"

MESON_VERSION_RE = re.compile(r"(^  version: ')(\d+\.\d+\.\d+)(')", re.MULTILINE)
CHANGELOG_SECTION_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]", re.MULTILINE)
# SSH：git@github.com:owner/repo.git；HTTPS：https://github.com/owner/repo.git
GITHUB_SLUG_RE = re.compile(r"github\.com[/:](.+?)(?:\.git)?/?$")

# 全量 workflow_dispatch 会展开矩阵，非 skipped 作业远多于单应用触发（常见 3～5 个）。
# REST/GraphQL 都不回传 inputs，只能靠作业规模区分 app=all 与单应用。
FULL_CI_MIN_JOBS = 20

# 汇报「HEAD 相对全量 CI 动过哪些应用目录」时用；黄灯只看工作流与锁文件。
APP_TOP_DIRS = (
    "programming",
    "artificial-intelligence",
    "computer-fundamentals",
    "electronics",
    "postgraduate",
    "guide",
    "mentor",
    "practice",
    "certification",
    "tools",
    "launcher",
    "packages",
)

SENSITIVE_EXACT = frozenset({"Cargo.lock", "pnpm-lock.yaml"})


@dataclass
class Finding:
    level: str  # 红 / 黄 / 绿
    title: str
    detail: str
    howto: str


GitRunner = Callable[..., str]
GhRunner = Callable[..., tuple[int, str, str]]


def run_git(args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败：{result.stderr.strip()}")
    return result.stdout


def run_gh(args: list[str]) -> tuple[int, str, str]:
    if shutil.which("gh") is None:
        return 127, "", "未安装 gh"
    result = subprocess.run(
        ["gh", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout, result.stderr


def force_utf8_output() -> None:
    """中文 Windows 控制台默认不是 UTF-8，体检中文会乱码或抛 UnicodeEncodeError。

    与 scripts/check.py 一样在入口重配标准流，不要求 ``-X utf8`` /
    PYTHONIOENCODING（ADR 0047）。``release.py readiness`` 与本模块
    ``main`` 都会调用。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def parse_github_slug(remote_url: str) -> str | None:
    match = GITHUB_SLUG_RE.search(remote_url.strip())
    return match.group(1) if match else None


def group_porcelain(porcelain: str) -> tuple[dict[str, int], dict[str, int]]:
    """按顶层目录分组：返回 (已修改计数, 未跟踪计数)。

    已修改含 staged/unstaged/重命名等；``??`` 单独进未跟踪。根目录文件归 ``(根)``。
    """
    modified: dict[str, int] = {}
    untracked: dict[str, int] = {}
    for raw in porcelain.splitlines():
        if not raw or len(raw) < 4:
            continue
        code, path = raw[:2], raw[3:]
        # porcelain 重命名：XY old -> new；分组看新路径
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        top = path.split("/", 1)[0] if "/" in path else "(根)"
        if code == "??":
            untracked[top] = untracked.get(top, 0) + 1
        else:
            modified[top] = modified.get(top, 0) + 1
    return modified, untracked


def format_groups(groups: dict[str, int]) -> str:
    if not groups:
        return "无"
    return "、".join(f"{k} {v}" for k, v in sorted(groups.items()))


def parse_ahead_behind(left_right: str) -> tuple[int, int]:
    """解析 ``git rev-list --left-right --count A...B`` 的 ``behind\\tahead``。"""
    text = left_right.strip()
    if not text:
        return 0, 0
    left, right = text.split()
    return int(left), int(right)


def parse_open_todos(text: str) -> list[str]:
    """抽出 ``- [ ]`` 条目原文（去掉前缀标记），不判断该不该做。"""
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            items.append(stripped[len("- [ ]") :].strip())
    return items


def next_patch_version(current: str) -> str:
    major, minor, patch = (int(p) for p in current.split("."))
    return f"{major}.{minor}.{patch + 1}"


def meson_version(text: str) -> str:
    match = MESON_VERSION_RE.search(text)
    if not match:
        raise ValueError("meson.build 里找不到 version")
    return match.group(2)


def changelog_has_version(text: str, version: str) -> bool:
    return version in CHANGELOG_SECTION_RE.findall(text)


def classify_touched(paths: list[str]) -> tuple[bool, bool, list[str]]:
    """返回 (动过工作流或锁文件, 动过应用目录, 应用顶层目录列表)。"""
    sensitive = False
    apps: list[str] = []
    seen: set[str] = set()
    for path in paths:
        norm = path.replace("\\", "/")
        if norm.startswith(".github/") or norm in SENSITIVE_EXACT:
            sensitive = True
        top = norm.split("/", 1)[0]
        if top in APP_TOP_DIRS and top not in seen:
            seen.add(top)
            apps.append(top)
    return sensitive, bool(apps), apps


def check_workspace(git: GitRunner) -> Finding:
    porcelain = git("status", "--porcelain")
    modified, untracked = group_porcelain(porcelain)
    total = sum(modified.values()) + sum(untracked.values())
    detail = (
        f"已修改：{format_groups(modified)}；未跟踪：{format_groups(untracked)}"
        if total
        else "工作区干净"
    )
    if total:
        return Finding(
            "红",
            "工作区",
            detail,
            "prepare 开头的体检有红即拒；先提交、stash，或确认未跟踪可清后再发版"
            "（紧急热修可 --skip-readiness）",
        )
    return Finding("绿", "工作区", detail, "")


def check_remote(git: GitRunner) -> Finding:
    # 只读：不 fetch。origin/main 过期时数字可能偏旧，提示使用者自己拉。
    probe = git("rev-parse", "--verify", "origin/main", check=False)
    if not probe.strip():
        return Finding(
            "黄",
            "与远端",
            "没有 origin/main 引用",
            "先 git fetch，再重跑 readiness；落后会挡 prepare",
        )
    behind, ahead = parse_ahead_behind(git("rev-list", "--left-right", "--count", "origin/main...main"))
    detail = f"main 相对 origin/main：超前 {ahead}、落后 {behind}（未 fetch，数字以本地引用为准）"
    if behind:
        return Finding(
            "红",
            "与远端",
            detail,
            "落后会挡 prepare；先 git pull --rebase（需要的话先 git fetch）",
        )
    if ahead:
        return Finding(
            "黄",
            "与远端",
            detail,
            "本地有未推送提交；发版前通常先 push，或确认这些提交要进本版",
        )
    return Finding("绿", "与远端", detail, "")


def _is_full_ci_run(gh: GhRunner, slug: str, run_id: int) -> bool | None:
    # 非 skipped 作业数；还在跑的 conclusion 为 null，也算进全量规模
    code, out, _err = gh(
        [
            "api",
            f"repos/{slug}/actions/runs/{run_id}/jobs?per_page=100",
            "--jq",
            "[.jobs[] | select(.conclusion != \"skipped\")] | length",
        ]
    )
    if code != 0:
        # 退一步：用 total_count，全量矩阵通常明显更大
        code2, out2, _err2 = gh(
            ["api", f"repos/{slug}/actions/runs/{run_id}/jobs?per_page=1", "--jq", ".total_count"]
        )
        if code2 != 0:
            return None
        try:
            return int(out2.strip()) >= FULL_CI_MIN_JOBS
        except ValueError:
            return None
    try:
        return int(out.strip()) >= FULL_CI_MIN_JOBS
    except ValueError:
        return None


def summarize_jobs(jobs: list[dict]) -> tuple[int, int, list[str]]:
    """已完成数、计入的作业总数、已失败的作业名。

    skipped 不计入：矩阵里被 if 跳过的格子不是这次要跑的。
    失败指 conclusion 已是 failure；还在跑的作业 conclusion 为空，不算失败。
    """
    counted = [job for job in jobs if (job.get("conclusion") or "") != "skipped"]
    done = sum(1 for job in counted if job.get("status") == "completed")
    failed = [
        str(job.get("name") or "(未命名)")
        for job in counted
        if job.get("conclusion") == "failure"
    ]
    return done, len(counted), failed


def _load_run_jobs(gh: GhRunner, slug: str, run_id: int) -> list[dict] | None:
    # run view 一次给出全部作业；api 的 per_page 会把大矩阵截断，进度会对不上。
    code, out, _err = gh(
        ["run", "view", str(run_id), f"--repo={slug}", "--json", "jobs"]
    )
    if code != 0:
        return None
    try:
        payload = json.loads(out or "{}")
    except json.JSONDecodeError:
        return None
    if isinstance(payload, list):
        jobs = payload
    elif isinstance(payload, dict):
        jobs = payload.get("jobs")
    else:
        return None
    if not isinstance(jobs, list):
        return None
    return jobs


def check_ci(git: GitRunner, gh: GhRunner) -> Finding:
    try:
        remote = git("remote", "get-url", "origin").strip()
    except RuntimeError as exc:
        return Finding("黄", "CI 全量验证", str(exc), "确认 origin 指向 GitHub 后再查")
    slug = parse_github_slug(remote)
    if not slug:
        return Finding(
            "黄",
            "CI 全量验证",
            f"无法从 origin URL 解析 owner/repo：{remote}",
            "gh 认不出非常规 remote；改为 github.com 的 HTTPS/SSH 地址，或手工查 Actions",
        )

    # 必须显式 --repo：SSH 形式的 origin 时 gh 自己推不出仓库
    code, out, err = gh(
        [
            "run",
            "list",
            "--workflow=ci.yml",
            f"--repo={slug}",
            "--event=workflow_dispatch",
            "--limit=30",
            "--json",
            "databaseId,status,conclusion,event,headSha,displayTitle,createdAt,updatedAt,url",
        ]
    )
    if code != 0:
        hint = (err or out or "gh 失败").strip()
        return Finding(
            "黄",
            "CI 全量验证",
            f"无法查询 gh（{hint}）",
            "安装并 gh auth login 后重跑；或到 GitHub Actions 手工确认最近一次 app=all 的 ci.yml",
        )

    try:
        runs = json.loads(out or "[]")
    except json.JSONDecodeError:
        return Finding("黄", "CI 全量验证", "gh 输出不是合法 JSON", "检查 gh 版本或改手工查 Actions")

    full = None
    unknown = 0
    for run in runs:
        flag = _is_full_ci_run(gh, slug, int(run["databaseId"]))
        if flag is True:
            full = run
            break
        if flag is None:
            unknown += 1

    if full is None:
        detail = "最近 30 次 workflow_dispatch 里没认出全量（app=all）run"
        if unknown:
            detail += f"；另有 {unknown} 次作业列表查失败"
        return Finding(
            "黄",
            "CI 全量验证",
            detail,
            "用 gh workflow run ci.yml -f app=all 跑一次全量，或放宽查询后再看",
        )

    run_id = full["databaseId"]
    sha = full.get("headSha") or ""
    status = full.get("status") or ""
    conclusion = full.get("conclusion") or ""
    updated = full.get("updatedAt") or full.get("createdAt") or ""
    url = full.get("url") or ""
    short = sha[:12] if sha else "?"

    commits_after = 0
    paths: list[str] = []
    if sha:
        commits_after = int(git("rev-list", "--count", f"{sha}..HEAD").strip() or "0")
        if commits_after:
            diff = git("diff", "--name-only", f"{sha}..HEAD")
            paths = [p for p in diff.splitlines() if p]

    sensitive, _apps_hit, app_dirs = classify_touched(paths)
    path_note = (
        f"HEAD 比该 run 新 {commits_after} 个提交"
        if sha
        else "无 headSha，算不了相对提交"
    )
    if commits_after:
        bits = []
        if sensitive:
            bits.append("其中动过 .github/ 或锁文件")
        if app_dirs:
            bits.append("动过应用目录：" + "、".join(app_dirs))
        if not bits:
            bits.append("未动工作流/锁文件/应用目录")
        path_note += "（" + "；".join(bits) + "）"

    detail = (
        f"run {run_id} · status={status} conclusion={conclusion or '—'} · "
        f"完成/更新 {updated} · commit {short} · {path_note}"
    )
    if url:
        detail += f" · {url}"

    # 大矩阵的 run 顶层会长时间停在 queued，里面的作业却已经在跑甚至失败。
    # 进行中不是失败：黄，并写出完成进度；红只留给整次 run 已结束且不是 success。
    jobs = _load_run_jobs(gh, slug, int(run_id))
    failed: list[str] = []
    if jobs is not None:
        done, total, failed = summarize_jobs(jobs)
        if status != "completed":
            progress = f"进行中：已完成 {done} / 共 {total} 个作业"
            if failed:
                progress += "；已失败：" + "、".join(failed)
            detail = progress + " · " + detail
    elif status != "completed":
        detail = "进行中：作业列表取不到（gh run view 失败） · " + detail

    if status != "completed":
        howto = "全量还在跑；等整次 run 结束再决定能不能发版"
        if failed:
            howto = "run 还没结束，但这些作业已经失败：" + "、".join(failed) + "。先看它们的日志"
        return Finding("黄", "CI 全量验证", detail, howto)
    if conclusion != "success":
        if failed:
            detail += "；已失败：" + "、".join(failed)
        return Finding(
            "红",
            "CI 全量验证",
            detail,
            "最近全量 ci.yml 已结束且不是 success；看失败作业或重新 gh workflow run ci.yml -f app=all",
        )
    if sensitive:
        return Finding(
            "黄",
            "CI 全量验证",
            detail,
            "全量绿之后又改了工作流或锁文件；发版前建议再跑一次全量 CI",
        )
    return Finding("绿", "CI 全量验证", detail, "")


def check_release_todo() -> Finding:
    if not RELEASE_TODO.is_file():
        return Finding("黄", "遗留清单", f"找不到 {RELEASE_TODO.relative_to(REPO_ROOT)}", "补文件或确认路径")
    items = parse_open_todos(RELEASE_TODO.read_text(encoding="utf-8"))
    if not items:
        return Finding("绿", "遗留清单", "没有未勾选项", "")
    listed = "\n".join(f"    - {item}" for item in items)
    return Finding(
        "黄",
        "遗留清单",
        f"{len(items)} 条未勾选（只列出，不判断该不该挡发版）：\n{listed}",
        "发版说明里别写成已完成；该收口的收口，其余留在下一版",
    )


def check_changelog() -> Finding:
    current = meson_version(MESON_BUILD.read_text(encoding="utf-8"))
    nxt = next_patch_version(current)
    text = CHANGELOG.read_text(encoding="utf-8")
    if changelog_has_version(text, nxt):
        return Finding("绿", "CHANGELOG", f"已有下一版 [{nxt}] 节（相对 meson {current} 的 patch+1）", "")
    return Finding(
        "黄",
        "CHANGELOG",
        f"还没有 [{nxt}] 节（相对 meson {current} 的 patch+1；若打算升 minor/major 另说）",
        "prepare 会按提交补机械底稿；也可先手写该节",
    )


def check_structure() -> Finding:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check.py"), "--sources-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    tail = (result.stdout or result.stderr or "").strip().splitlines()
    summary = tail[-1] if tail else f"exit {result.returncode}"
    if result.returncode != 0:
        return Finding(
            "红",
            "结构检查",
            f"check.py --sources-only 失败：{summary}",
            "先修跨应用检查，再 prepare",
        )
    return Finding("绿", "结构检查", f"check.py --sources-only 通过：{summary}", "")


def render(findings: list[Finding], out: TextIO) -> int:
    reds = sum(1 for f in findings if f.level == "红")
    yellows = sum(1 for f in findings if f.level == "黄")
    for finding in findings:
        out.write(f"[{finding.level}] {finding.title}：{finding.detail}\n")
        if finding.howto:
            out.write(f"       怎么处理：{finding.howto}\n")
    if reds:
        out.write(f"\n结论：有 {reds} 项红" + (f" / 有 {yellows} 项黄" if yellows else "") + "\n")
        return 1
    if yellows:
        out.write(f"\n结论：有 {yellows} 项黄（无红，可以准备 prepare，先看黄项）\n")
        return 0
    out.write("\n结论：可以 prepare\n")
    return 0


def collect_findings(
    *,
    with_checks: bool = False,
    git: GitRunner | None = None,
    gh: GhRunner | None = None,
) -> list[Finding]:
    """与 readiness 子命令同一套检查。prepare 只看这里的红黄，不再另判工作区与远端。"""
    git_fn: GitRunner = git or (lambda *a, check=True: run_git(list(a), check=check))
    gh_fn: GhRunner = gh or run_gh
    findings = [
        check_workspace(git_fn),
        check_remote(git_fn),
        check_ci(git_fn, gh_fn),
        check_release_todo(),
        check_changelog(),
    ]
    if with_checks:
        findings.append(check_structure())
    return findings


def run_readiness(
    *,
    with_checks: bool = False,
    out: TextIO | None = None,
    git: GitRunner | None = None,
    gh: GhRunner | None = None,
) -> int:
    out = out or sys.stdout
    return render(collect_findings(with_checks=with_checks, git=git, gh=gh), out)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    with_checks = False
    if "--with-checks" in argv:
        with_checks = True
        argv = [a for a in argv if a != "--with-checks"]
    if argv:
        print(f"未知参数：{' '.join(argv)}", file=sys.stderr)
        return 2
    force_utf8_output()
    return run_readiness(with_checks=with_checks)


if __name__ == "__main__":
    sys.exit(main())
