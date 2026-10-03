#!/usr/bin/env python3
"""一键发版（ADR 0081）：统一 tag、全量构建、单个 Athena Release。

CI（.github/workflows/release.yml）已经包揽构建、打包、发布和拾阶更新通道的
同步；剩下的手工活只有三样——定版本号、升 meson 版本、写 CHANGELOG 节。这个
脚本把它们收进两条命令，machine 汇编线之类的内容工作照旧不受发版影响。

用法：
  python3 scripts/release.py prepare --patch              # 8.0.0 → 8.0.1
  python3 scripts/release.py prepare --minor              # 8.0.0 → 8.1.0
  python3 scripts/release.py prepare --major              # 8.0.0 → 9.0.0
  python3 scripts/release.py prepare 8.2.0                # 显式给版本号
  python3 scripts/release.py prepare --patch --dry-run    # 只预览，不动任何文件
  python3 scripts/release.py push                         # 第二阶段：推送并触发 CI
  python3 scripts/release.py push 8.2.0                   # push 时显式指定版本

两阶段，中间留人工润色的位置：
  1. prepare：校验前提（main、干净、与远端同步、版本只增、tag 未占用）→
     bump subjects/cpp/meson.build → CHANGELOG 缺节时按提交预生成 →
     提交「chore(release): x.y.z」→ 打 tag v x.y.z。
     自动生成的 CHANGELOG 只是提交标题的堆砌；想润色就编辑后
     `git commit --amend --no-edit && git tag -f v x.y.z`。
  2. push：确认 tag 指向 HEAD → `git push origin main v x.y.z` →
     打印查看 CI 的命令。此后构建与发布全部由 CI 接手。

meson 版本必须预提交：release.yml 三个 cpp job 都用 tag 校验 meson 版本，
这是既有的防呆（tag 与构建物必须一致）。driver、拾阶的版本由 CI 从 tag
写入各自的清单文件，不需要（也不应该）在仓库里追着 tag 改。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MESON_BUILD = REPO_ROOT / "subjects/cpp/meson.build"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
CHANGELOG_NOTES = REPO_ROOT / "subjects/cpp/scripts/changelog_notes.py"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
MESON_VERSION_RE = re.compile(r"(^  version: ')(\d+\.\d+\.\d+)(')", re.MULTILINE)
CHANGELOG_SECTION_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]", re.MULTILINE)


def run(args: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args, cwd=REPO_ROOT, capture_output=capture, text=True, encoding="utf-8", errors="replace"
    )
    return result


def git(*args: str, check: bool = True) -> str:
    result = run(["git", *args])
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} 失败：\n{result.stderr.strip()}")
    return result.stdout.strip()


def die(message: str) -> None:
    sys.exit(f"✗ {message}")


def current_meson_version() -> str:
    match = MESON_VERSION_RE.search(MESON_BUILD.read_text(encoding="utf-8"))
    if not match:
        die(f"{MESON_BUILD.relative_to(REPO_ROOT)} 里找不到 project() 的 version 行")
    return match.group(2)


def parse_target(args: argparse.Namespace) -> str:
    if args.version:
        target = args.version
    else:
        major, minor, patch = (int(part) for part in current_meson_version().split("."))
        if args.major:
            major += 1
        elif args.minor:
            minor += 1
        else:
            patch += 1
        target = f"{major}.{minor}.{patch}"
    if not VERSION_RE.match(target):
        die(f"版本号 '{target}' 不是 x.y.z 形式")
    return target


def check_prerequisites(target: str) -> None:
    if git("branch", "--show-current") != "main":
        die("不在 main 分支上；发版从 main 出")
    # 未跟踪文件不挡发版：提交只 add 指定的两个文件，另一条工作线的草稿不受影响
    if git("status", "--porcelain", "--untracked-files=no"):
        die("有已跟踪文件未提交；先提交或 stash")
    if git("rev-list", "--count", "origin/main..main") != "0" or git(
        "rev-list", "--count", "main..origin/main"
    ) != "0":
        die("main 与 origin/main 不同步；先 git pull --rebase / git push")
    current = current_meson_version()
    if tuple(int(p) for p in target.split(".")) <= tuple(int(p) for p in current.split(".")):
        die(f"目标版本 {target} 不大于当前 meson 版本 {current}；版本只增不减")
    if git("rev-parse", "-q", "--verify", f"refs/tags/v{target}", check=False):
        die(f"tag v{target} 已存在")
    remote = run(["git", "ls-remote", "--exit-code", "origin", f"refs/tags/v{target}"])
    if remote.returncode == 0:
        die(f"远端已有 tag v{target}")
    if remote.returncode > 1:
        print("⚠ 查不到远端（离线？）；远端是否已有同名 tag 留给 push 兜底", flush=True)


def bump_meson(target: str, dry_run: bool) -> None:
    text = MESON_BUILD.read_text(encoding="utf-8")
    new_text, count = MESON_VERSION_RE.subn(rf"\g<1>{target}\g<3>", text, count=1)
    if count != 1:
        die("meson.build 的 version 行替换失败")
    if dry_run:
        print(f"  [dry] {MESON_BUILD.relative_to(REPO_ROOT)}：version → {target}")
        return
    MESON_BUILD.write_text(new_text, encoding="utf-8")
    print(f"  {MESON_BUILD.relative_to(REPO_ROOT)}：version → {target}", flush=True)


def ensure_changelog(target: str, dry_run: bool) -> None:
    sections = CHANGELOG_SECTION_RE.findall(CHANGELOG.read_text(encoding="utf-8"))
    if target in sections:
        print(f"  CHANGELOG 已有 [{target}] 节，原样保留", flush=True)
        return
    if dry_run:
        print(f"  [dry] CHANGELOG 预生成 [{target}] 节（changelog_notes.py --write）")
        return
    result = run([sys.executable, str(CHANGELOG_NOTES), target, str(CHANGELOG), "--write"])
    if result.returncode != 0:
        die(f"CHANGELOG 预生成失败：\n{result.stderr.strip()}")
    print("  CHANGELOG 预生成了 [" + target + "] 节——是提交标题的堆砌，建议润色后再 push", flush=True)


def prepare(target: str, dry_run: bool) -> None:
    print(f"发版准备 {target}：", flush=True)
    check_prerequisites(target)
    bump_meson(target, dry_run)
    ensure_changelog(target, dry_run)
    if dry_run:
        print("dry-run 结束，未做任何改动。")
        return
    git("add", str(MESON_BUILD), str(CHANGELOG))
    git("commit", "-m", f"chore(release): {target}")
    git("tag", f"v{target}")
    print(
        f"已提交并打 tag v{target}。接下来：\n"
        f"  · 润色 CHANGELOG（可选）：编辑后 git commit --amend --no-edit && git tag -f v{target}\n"
        f"  · 确认无误：python3 scripts/release.py push",
        flush=True,
    )


def push(target: str | None) -> None:
    tag = f"v{target}" if target else git("describe", "--tags", "--abbrev=0")
    if not VERSION_RE.match(tag.lstrip("v")):
        die(f"最近的 tag '{tag}' 不是发版 tag；push 需要显式版本：release.py push <版本>")
    if git("rev-parse", tag) != git("rev-parse", "HEAD"):
        die(f"{tag} 没有指向 HEAD（amend 过就先 git tag -f {tag}）")
    ahead = git("rev-list", "--count", f"origin/main..{tag}")
    if ahead == "0":
        die(f"{tag} 已经在远端；无需推送")
    git("push", "origin", "main", tag)
    # 兼容 https 与 ssh 两种 remote 写法；识别不了就不猜 URL
    match = re.search(r"github\.com[/:](.+?)(?:\.git)?/?$", git("remote", "get-url", "origin"))
    where = (
        f"完成后 Release 在 https://github.com/{match.group(1)}/releases/latest"
        if match
        else "完成后 Release 见仓库的 Releases 页"
    )
    print(
        f"已推送 {tag}。CI 全量构建中，查看进度：\n"
        "  gh run watch --exit-status $(gh run list --workflow=release.yml --limit 1 "
        "--json databaseId --jq '.[0].databaseId')\n" + where,
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="一键发版（ADR 0081），详见文件头 docstring")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare", help="第一阶段：bump 版本、预生成 CHANGELOG、打 tag")
    target = p_prepare.add_mutually_exclusive_group()
    target.add_argument("--major", action="store_true", help="主版本 +1")
    target.add_argument("--minor", action="store_true", help="次版本 +1")
    target.add_argument("--patch", action="store_true", help="修订号 +1")
    target.add_argument("version", nargs="?", help="显式版本号 x.y.z")
    p_prepare.add_argument("--dry-run", action="store_true", help="只预览要做的改动")

    p_push = sub.add_parser("push", help="第二阶段：推送 main 与发版 tag，触发 CI")
    p_push.add_argument("version", nargs="?", help="显式版本号（默认取最近的发版 tag）")

    args = parser.parse_args()
    if args.command == "push":
        push(args.version)
    else:
        if args.version and (args.major or args.minor or args.patch):
            p_prepare.error("显式版本号与 --major/--minor/--patch 别同时给")
        if not args.version and not (args.major or args.minor or args.patch):
            p_prepare.error("给一个版本号，或 --major/--minor/--patch 之一")
        prepare(parse_target(args), args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
