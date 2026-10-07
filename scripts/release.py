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

两阶段，中间不需要人工：
  1. prepare：校验前提（main、干净、与远端同步、版本只增、tag 未占用）→
     bump subjects/cpp/meson.build → CHANGELOG 缺节时先按提交生成机械底稿，
     再交给 GLM 对照上一版的手写风格总结润色（不是提交标题堆砌）→
     提交「chore(release): x.y.z」→ 打 tag v x.y.z。
  2. push：确认 tag 指向 HEAD → `git push origin main v x.y.z` →
     打印查看 CI 的命令。此后构建与发布全部由 CI 接手。

AI 润色的降级链（任何一步失败都保留机械底稿，不阻塞发版）：
  · 没设 ZAI_API_KEY → 跳过润色，底稿留待手工或 agent 会话里改写；
  · API 调用失败（网络、额度、模型名）→ 警告并保留底稿；
模型用 --model 或环境变量 ATHENA_RELEASE_MODEL 覆盖，默认 glm-4.7-flash。
在 agent 会话里发版时也可以不让脚本润色，由 agent 直接改写后再提交。

meson 版本必须预提交：release.yml 三个 cpp job 都用 tag 校验 meson 版本，
这是既有的防呆（tag 与构建物必须一致）。driver、拾阶的版本由 CI 从 tag
写入各自的清单文件，不需要（也不应该）在仓库里追着 tag 改。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MESON_BUILD = REPO_ROOT / "subjects/cpp/meson.build"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
CHANGELOG_NOTES = REPO_ROOT / "subjects/cpp/scripts/changelog_notes.py"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
MESON_VERSION_RE = re.compile(r"(^  version: ')(\d+\.\d+\.\d+)(')", re.MULTILINE)
CHANGELOG_SECTION_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]", re.MULTILINE)
SECTION_BLOCK_RE = re.compile(
    r"^## \[(\d+\.\d+\.\d+)\][^\n]*\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
ZAI_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4.7-flash"


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


def extract_section(target: str) -> str:
    for match in SECTION_BLOCK_RE.finditer(CHANGELOG.read_text(encoding="utf-8")):
        if match.group(1) == target:
            return match.group(2).strip()
    return ""


def replace_section(target: str, body: str) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    for match in SECTION_BLOCK_RE.finditer(text):
        if match.group(1) != target:
            continue
        title_end = text.index("\n", match.start()) + 1
        CHANGELOG.write_text(text[:title_end] + body.strip() + "\n" + text[match.end():], encoding="utf-8")
        return


def ai_polish(target: str, model: str) -> str | None:
    """把机械底稿交给 GLM 对照上一版手写风格重写；失败一律返回 None 保留底稿。"""
    key = os.environ.get("ZAI_API_KEY")
    if not key:
        print("  ⚠ 未设 ZAI_API_KEY，跳过 AI 润色，CHANGELOG 保留机械底稿", flush=True)
        return None
    draft = extract_section(target)
    style_sample = next(
        (m.group(2).strip() for m in SECTION_BLOCK_RE.finditer(CHANGELOG.read_text(encoding="utf-8")) if m.group(1) != target),
        "",
    )
    system = (
        "你是 Athena 仓库的发版编辑。把 CHANGELOG 某一版的机械汇总改写成可读的发版说明："
        "提炼主线（哪几条工作线各自做成了什么），合并同一主题的多个提交，每条用人话写；"
        "保留小节分类结构（如「### 驾考 subjects/driver」「### 启动器与基础设施」「### 文档」），按内容归属分类；"
        "不出现 feat/fix 等提交前缀，不编造提交里没有的内容，全文中文。"
        "只输出该节正文，不要标题行和代码围栏。"
    )
    user = f"版本：{target}\n\n【上一版手写节（风格基准）】\n{style_sample}\n\n【本版机械底稿】\n{draft}"
    body = json.dumps(
        {
            "model": model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    request = urllib.request.Request(
        ZAI_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            content = json.load(response)["choices"][0]["message"]["content"]
    except (urllib.error.URLError, OSError, KeyError, IndexError, json.JSONDecodeError) as error:
        print(f"  ⚠ AI 润色调用失败（{error}），保留机械底稿", flush=True)
        return None
    content = content.strip()
    content = re.sub(r"^```(?:markdown)?\n|\n```$", "", content).strip()
    if not content or "## [" in content:
        print("  ⚠ AI 润色结果不合格（越权改标题），保留机械底稿", flush=True)
        return None
    return content


def ensure_changelog(target: str, model: str, dry_run: bool) -> None:
    sections = CHANGELOG_SECTION_RE.findall(CHANGELOG.read_text(encoding="utf-8"))
    if target in sections:
        print(f"  CHANGELOG 已有 [{target}] 节，原样保留", flush=True)
        return
    if dry_run:
        polish = "GLM 润色" if os.environ.get("ZAI_API_KEY") else "机械底稿（未设 ZAI_API_KEY）"
        print(f"  [dry] CHANGELOG 生成 [{target}] 节：changelog_notes.py 底稿 + {polish}")
        return
    result = run([sys.executable, str(CHANGELOG_NOTES), target, str(CHANGELOG), "--write"])
    if result.returncode != 0:
        die(f"CHANGELOG 底稿生成失败：\n{result.stderr.strip()}")
    polished = ai_polish(target, model)
    if polished:
        replace_section(target, polished)
        print(f"  CHANGELOG [{target}] 节已由 {model} 对照上一版风格总结润色", flush=True)
    else:
        print(f"  CHANGELOG [{target}] 节保留机械底稿，可手工或由 agent 会话改写", flush=True)


def github_slug() -> str | None:
    # 兼容 https 与 ssh 两种 remote 写法；识别不了就不猜 URL
    match = re.search(r"github\.com[/:](.+?)(?:\.git)?/?$", git("remote", "get-url", "origin"))
    return match.group(1) if match else None


def tidy_changelog(target: str, dry_run: bool) -> None:
    """把本版标题与对比链接收成 Keep a Changelog 的写法。

    手写或 agent 改写时常把标题写成 ``## [X.Y.Z](日期)``——那是 Markdown 链接
    语法，渲染出来是一个指向日期的坏链接；文末的 ``[X.Y.Z]: compare`` 定义也
    总被漏掉，标题就成了带方括号的纯文本。两处都是机械规则，发版时顺手补齐。
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    fixed = re.sub(
        r"^## \[(\d+\.\d+\.\d+)\]\((\d{4}-\d{2}-\d{2})\)[ \t]*$", r"## [\1] - \2", text, flags=re.MULTILINE
    )
    slug = github_slug()
    if slug and not re.search(rf"^\[{re.escape(target)}\]: ", fixed, flags=re.MULTILINE):
        versions = CHANGELOG_SECTION_RE.findall(fixed)  # 文件里新版在前
        older = versions[versions.index(target) + 1 :] if target in versions else []
        base = f"https://github.com/{slug}"
        url = f"{base}/compare/v{older[0]}...v{target}" if older else f"{base}/releases/tag/v{target}"
        definition = f"[{target}]: {url}\n"
        first = re.search(r"^\[\d+\.\d+\.\d+\]: ", fixed, flags=re.MULTILINE)
        fixed = (
            fixed[: first.start()] + definition + fixed[first.start() :]
            if first
            else fixed.rstrip("\n") + "\n\n" + definition
        )
    if fixed == text:
        return
    if dry_run:
        print(f"  [dry] CHANGELOG 规整 [{target}] 的标题写法与对比链接", flush=True)
        return
    CHANGELOG.write_text(fixed, encoding="utf-8", newline="\n")
    print(f"  CHANGELOG 已规整 [{target}] 的标题写法与对比链接", flush=True)


def prepare(target: str, model: str, dry_run: bool) -> None:
    print(f"发版准备 {target}：", flush=True)
    check_prerequisites(target)
    bump_meson(target, dry_run)
    ensure_changelog(target, model, dry_run)
    tidy_changelog(target, dry_run)
    if dry_run:
        print("dry-run 结束，未做任何改动。")
        return
    git("add", str(MESON_BUILD), str(CHANGELOG))
    git("commit", "-m", f"chore(release): {target}")
    git("tag", f"v{target}")
    print(
        f"已提交并打 tag v{target}。接下来：\n"
        f"  · 过目 CHANGELOG 的 [{target}] 节，不合意就编辑后 git commit --amend --no-edit && git tag -f v{target}\n"
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
    slug = github_slug()
    where = (
        f"完成后 Release 在 https://github.com/{slug}/releases/latest"
        if slug
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

    p_prepare = sub.add_parser("prepare", help="第一阶段：bump 版本、AI 润色 CHANGELOG、打 tag")
    target = p_prepare.add_mutually_exclusive_group()
    target.add_argument("--major", action="store_true", help="主版本 +1")
    target.add_argument("--minor", action="store_true", help="次版本 +1")
    target.add_argument("--patch", action="store_true", help="修订号 +1")
    target.add_argument("version", nargs="?", help="显式版本号 x.y.z")
    p_prepare.add_argument("--dry-run", action="store_true", help="只预览要做的改动")
    p_prepare.add_argument(
        "--model",
        default=os.environ.get("ATHENA_RELEASE_MODEL", DEFAULT_MODEL),
        help=f"CHANGELOG 润色用的模型（默认 {DEFAULT_MODEL}，可用环境变量 ATHENA_RELEASE_MODEL 覆盖）",
    )

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
        prepare(parse_target(args), args.model, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
