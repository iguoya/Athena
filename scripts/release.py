#!/usr/bin/env python3
"""一键发版（ADR 0081、0171）：一个 tag 一次发版，只构建有改动的应用，应用各有自己的版本号。

CI（.github/workflows/release.yml）已经包揽构建、打包、发布和拾阶更新通道的
同步；剩下的手工活只有三样——定发版号、升有改动应用的版本、写 CHANGELOG 节。
这个脚本把它们收进两条命令，machine 汇编线之类的内容工作照旧不受发版影响。

发版号写在仓库根 VERSION；每个应用的真实版本写在各自的清单里（tauri.conf.json、
pubspec.yaml、meson.build、package.json）。哪些应用有改动、该升到几，由
scripts/release_plan.py 算（依赖图只在这里算，CI 只比较清单里的版本）。

用法：
  python3 scripts/release.py prepare --patch              # 8.0.0 → 8.0.1
  python3 scripts/release.py prepare --minor              # 8.0.0 → 8.1.0
  python3 scripts/release.py prepare --major              # 8.0.0 → 9.0.0
  python3 scripts/release.py prepare 8.2.0                # 显式给版本号
  python3 scripts/release.py prepare --patch --dry-run    # 只预览（含各应用升版本的计划表），不动任何文件
  python3 scripts/release.py prepare --minor --bump snake=minor --bump driver=10.2.0
                                                          # 手动覆盖某个应用建议的升级档或版本
  python3 scripts/release.py prepare --patch --skip-readiness  # 紧急热修，跳过体检
  python3 scripts/release.py push                         # 第二阶段：推送并触发 CI
  python3 scripts/release.py push 8.2.0                   # push 时显式指定版本
  python3 scripts/release.py readiness                    # 发版前只读体检（见 release_readiness.py）
  python3 scripts/release.py readiness --with-checks      # 顺带跑 check.py --sources-only

两阶段，中间不需要人工：
  1. prepare：开头跑发版体检（release_readiness；有红即拒，黄只打印；
     --dry-run 下红只提示不拒；紧急热修可 --skip-readiness）→
     再校验 readiness 未覆盖的前提（只能在 main、版本只增、tag 未占用）→
     按计划升有改动应用的清单版本、写 VERSION → CHANGELOG 缺节时先按提交生成机械底稿，
     再交给 GLM 对照上一版的手写风格总结润色（不是提交标题堆砌）→
     提交「chore(release): x.y.z」→ 打 tag v x.y.z。
     工作区干净、与远端同步的口径只在 readiness 里判一次，不在这里重复。
  2. push：确认 tag 指向 HEAD → `git push origin main v x.y.z` →
     打印查看 CI 的命令。此后构建与发布全部由 CI 接手。

AI 润色的降级链（任何一步失败都保留机械底稿，不阻塞发版）：
  · 没设 ZAI_API_KEY → 跳过润色，底稿留待手工或 agent 会话里改写；
  · API 调用失败（网络、额度、模型名）→ 警告并保留底稿；
模型用 --model 或环境变量 ATHENA_RELEASE_MODEL 覆盖，默认 glm-4.7-flash。
在 agent 会话里发版时也可以不让脚本润色，由 agent 直接改写后再提交。

各应用的版本必须预提交：CI 的 plan 作业按「清单版本与上一个 tag 不同」决定构建谁，
构建作业再读清单版本给安装包命名，不再用 tag 覆盖（ADR 0171）。
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
VERSION_FILE = REPO_ROOT / "VERSION"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
CHANGELOG_NOTES = REPO_ROOT / "practice/cpp/scripts/changelog_notes.py"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
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


def current_release_version() -> str:
    """上一次发布的发版号，写在仓库根 VERSION（一行 x.y.z）。"""
    if not VERSION_FILE.is_file():
        die("仓库根没有 VERSION；先建它，内容写上一个发布的版本号（例如 10.0.0）")
    value = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(value):
        die(f"VERSION 里的 '{value}' 不是 x.y.z 形式")
    return value


def parse_target(args: argparse.Namespace) -> str:
    if args.version:
        target = args.version
    else:
        major, minor, patch = (int(part) for part in current_release_version().split("."))
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


def gate_on_readiness(
    *,
    dry_run: bool,
    skip: bool,
    readiness_runner=None,
    git=None,
    gh=None,
    plan=None,
) -> None:
    """prepare 开头的发版体检门禁。

    工作区干净、与远端同步等口径只在 release_readiness 里判；这里只决定
    红/黄/dry-run/skip 怎么影响 prepare。readiness_runner 供自测注入桩。
    """
    if skip:
        # 醒目警告：逃生口必须显式写出，避免习惯性跳过
        print("⚠ 已跳过发版体检（--skip-readiness）", flush=True)
        return
    runner = readiness_runner
    if runner is None:
        from release_readiness import force_utf8_output, run_readiness

        force_utf8_output()

        def runner() -> int:
            return run_readiness(with_checks=False, git=git, gh=gh, plan=plan)

    code = runner()
    if code == 0:
        return
    # code != 0：体检已打印红项表。dry-run 要预览改动，只提示不拒。
    if dry_run:
        print(
            "⚠ dry-run：发版体检有红项，仅提示、不拒绝（要预览改动）。"
            "真正 prepare 前请先处理红项。",
            flush=True,
        )
        return
    die(
        "发版体检有红项，已拒绝 prepare。"
        "按上表「怎么处理」修好后重跑；紧急热修可显式加 --skip-readiness"
    )


def check_prerequisites(target: str) -> None:
    """readiness 未覆盖的前提：分支、版本单调、tag 未占用。

    工作区干净、与远端同步已改由 gate_on_readiness → release_readiness 判，
    这里不再重复，避免两处口径各说各话。
    """
    if git("branch", "--show-current") != "main":
        die("不在 main 分支上；发版从 main 出")
    current = current_release_version()
    if tuple(int(p) for p in target.split(".")) <= tuple(int(p) for p in current.split(".")):
        die(f"目标版本 {target} 不大于当前 VERSION {current}；版本只增不减")
    if git("rev-parse", "-q", "--verify", f"refs/tags/v{target}", check=False):
        die(f"tag v{target} 已存在")
    remote = run(["git", "ls-remote", "--exit-code", "origin", f"refs/tags/v{target}"])
    if remote.returncode == 0:
        die(f"远端已有 tag v{target}")
    if remote.returncode > 1:
        print("⚠ 查不到远端（离线？）；远端是否已有同名 tag 留给 push 兜底", flush=True)


def write_release_version(target: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry] VERSION：{current_release_version()} → {target}")
        return
    VERSION_FILE.write_text(target + chr(10), encoding="utf-8", newline="")
    print(f"  VERSION：→ {target}", flush=True)


def parse_bump_overrides(items: list[str]) -> dict[str, str]:
    """--bump 应用=major|minor|patch|x.y.z，可重复；重复指定同一应用以后一次为准。"""
    overrides: dict[str, str] = {}
    for item in items:
        app, sep, value = item.partition("=")
        if not sep or not app or not value:
            die(f"--bump 要写成 应用=档位或版本（例：snake=minor、driver=10.2.0），收到 '{item}'")
        overrides[app] = value
    return overrides


def plan_release(overrides: dict[str, str]) -> tuple[list[dict], list[dict], str]:
    """按 release_plan 算本次发版：返回（要写进清单的版本变更，新应用，base tag）。

    只在 prepare 里写文件；这里只算。已经升过版本的应用不再升（重跑 prepare 要幂等）。
    """
    import release_plan

    base = release_plan.latest_version_tag(REPO_ROOT)
    apps = release_plan.load_apps()
    by_id = {app["id"]: app for app in apps}
    decisions = release_plan.compute_decisions(REPO_ROOT, apps, base, "HEAD")
    changes: list[dict] = []
    fresh: list[dict] = []
    pending = dict(overrides)
    for decision in decisions:
        if not decision["changed"]:
            continue
        if decision["new"]:
            fresh.append(decision)
            continue
        if decision["bump"] == "none":
            continue
        app = by_id[decision["id"]]
        current = decision["current"]
        target_version = decision["suggested"]
        level = decision["bump"]
        override = pending.pop(decision["id"], None)
        if override is not None:
            if override in ("major", "minor", "patch"):
                target_version = release_plan.apply_bump(current, override)
                level = override
            elif release_plan.SEMVER_RE.match(override):
                target_version = override
                level = "手动指定"
            else:
                die(f"--bump {decision['id']}={override}：不是 major/minor/patch，也不是 x.y.z")
            if release_plan.core_version(target_version) == release_plan.core_version(current):
                die(f"--bump {decision['id']}={override}：结果 {target_version} 没有高于当前 {current}")
        changes.append(
            {
                "id": decision["id"],
                "manifest": app["manifest"],
                "format": app["manifest_format"],
                "old": current,
                "new": target_version,
                "level": level,
                "reasons": decision["reasons"],
            }
        )
    if pending:
        names = "、".join(sorted(pending))
        die(
            f"--bump 指定了 {names}，但它们不在待升版本的名单里"
            "（没有改动、是新应用，或清单版本已经升过）；用 prepare --dry-run 看计划表"
        )
    if not changes and not fresh:
        die(f"相对 {base} 没有任何应用有改动，没有可发布的内容")
    return changes, fresh, base


def print_release_plan(changes: list[dict], fresh: list[dict], base: str) -> None:
    print(f"  相对 {base} 的应用版本计划：", flush=True)
    for change in changes:
        print(f"    {change['id']}: {change['old']} → {change['new']}（{change['level']}）", flush=True)
    for decision in fresh:
        print(f"    {decision['id']}: {decision['current']}（新应用，首发，不升）", flush=True)


def apply_release_plan(changes: list[dict], dry_run: bool) -> list[str]:
    """把新版本写进各应用清单，只改版本那一处。返回改动的清单路径（相对仓库根）。"""
    import release_plan

    written: list[str] = []
    for change in changes:
        path = REPO_ROOT / change["manifest"]
        data = path.read_bytes()
        updated = release_plan.write_version(data, change["format"], change["new"])
        if dry_run:
            print(f"  [dry] {change['manifest']}：{change['old']} → {change['new']}")
            continue
        path.write_bytes(updated)
        written.append(change["manifest"])
    if not dry_run:
        print(f"  已把 {len(written)} 个应用的清单版本升到新值", flush=True)
    return written


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
        "保留小节分类结构（如「### 驾考 certification/driver」「### 启动器与基础设施」「### 文档」），按内容归属分类；"
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


def check_version_level(target: str) -> None:
    """对照 CHANGELOG 文件头的约定：有 ⚠️ 条目升主版本，没有就升次版本或修订号。

    只提醒不拦：⚠️ 是人写的判断，机械底稿里不会有，拦下来反而逼人乱标。
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    versions = CHANGELOG_SECTION_RE.findall(text)
    if target not in versions or versions.index(target) + 1 >= len(versions):
        return
    previous = versions[versions.index(target) + 1]
    body = next((m.group(2) for m in SECTION_BLOCK_RE.finditer(text) if m.group(1) == target), "")
    is_major = target.split(".")[0] != previous.split(".")[0]
    breaking = "⚠️" in body
    if is_major and not breaking:
        print(
            f"  ⚠ {previous} → {target} 升了主版本，但本节没有 ⚠️ 条目：要么补上不兼容变更的标记，"
            "要么改发次版本（--minor）或修订号（--patch）",
            flush=True,
        )
    elif breaking and not is_major:
        print(
            f"  ⚠ 本节有 ⚠️ 条目（不兼容变更），按约定 {previous} 之后应升主版本（--major）",
            flush=True,
        )


def prepare(
    target: str,
    model: str,
    dry_run: bool,
    *,
    skip_readiness: bool = False,
    readiness_runner=None,
    bump_overrides: dict[str, str] | None = None,
) -> None:
    print(f"发版准备 {target}：", flush=True)
    gate_on_readiness(
        dry_run=dry_run,
        skip=skip_readiness,
        readiness_runner=readiness_runner,
    )
    check_prerequisites(target)
    changes, fresh, base = plan_release(bump_overrides or {})
    print_release_plan(changes, fresh, base)
    write_release_version(target, dry_run)
    manifests = apply_release_plan(changes, dry_run)
    ensure_changelog(target, model, dry_run)
    tidy_changelog(target, dry_run)
    check_version_level(target)
    if dry_run:
        print("dry-run 结束，未做任何改动。")
        return
    git("add", "--", str(VERSION_FILE), str(CHANGELOG), *[str(REPO_ROOT / path) for path in manifests])
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
        f"已推送 {tag}。CI 按计划构建有改动的应用，查看进度：\n"
        "  gh run watch --exit-status $(gh run list --workflow=release.yml --limit 1 "
        "--json databaseId --jq '.[0].databaseId')\n" + where,
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="一键发版（ADR 0081、0171），详见文件头 docstring")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare", help="第一阶段：bump 版本、AI 润色 CHANGELOG、打 tag")
    target = p_prepare.add_mutually_exclusive_group()
    target.add_argument("--major", action="store_true", help="主版本 +1")
    target.add_argument("--minor", action="store_true", help="次版本 +1")
    target.add_argument("--patch", action="store_true", help="修订号 +1")
    target.add_argument("version", nargs="?", help="显式版本号 x.y.z")
    p_prepare.add_argument("--dry-run", action="store_true", help="只预览要做的改动")
    p_prepare.add_argument(
        "--bump",
        action="append",
        default=[],
        metavar="应用=档位或版本",
        help="覆盖某个应用建议的版本（major/minor/patch 或 x.y.z），可重复；先用 --dry-run 看计划表",
    )
    p_prepare.add_argument(
        "--skip-readiness",
        action="store_true",
        help="跳过发版体检（紧急热修逃生口；会打印醒目警告）",
    )
    p_prepare.add_argument(
        "--model",
        default=os.environ.get("ATHENA_RELEASE_MODEL", DEFAULT_MODEL),
        help=f"CHANGELOG 润色用的模型（默认 {DEFAULT_MODEL}，可用环境变量 ATHENA_RELEASE_MODEL 覆盖）",
    )

    p_push = sub.add_parser("push", help="第二阶段：推送 main 与发版 tag，触发 CI")
    p_push.add_argument("version", nargs="?", help="显式版本号（默认取最近的发版 tag）")

    p_ready = sub.add_parser(
        "readiness",
        help="发版前只读体检：工作区、远端、CI 全量、遗留清单、CHANGELOG",
    )
    p_ready.add_argument(
        "--with-checks",
        action="store_true",
        help="顺带跑 python scripts/check.py --sources-only（默认不跑，较慢）",
    )

    args = parser.parse_args()
    if args.command == "push":
        push(args.version)
        return 0
    if args.command == "readiness":
        # 逻辑单独放 release_readiness.py，这里只转调，避免动到 prepare/push。
        # utf-8 放在这个子命令入口：中文 Windows 默认编码会把体检输出打成乱码。
        from release_readiness import force_utf8_output, run_readiness

        force_utf8_output()
        return run_readiness(with_checks=args.with_checks)
    if args.version and (args.major or args.minor or args.patch):
        p_prepare.error("显式版本号与 --major/--minor/--patch 别同时给")
    if not args.version and not (args.major or args.minor or args.patch):
        p_prepare.error("给一个版本号，或 --major/--minor/--patch 之一")
    prepare(
        parse_target(args),
        args.model,
        args.dry_run,
        skip_readiness=args.skip_readiness,
        bump_overrides=parse_bump_overrides(args.bump),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
