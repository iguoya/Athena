"""PreToolUse hook：拦下会把别人改动一起卷进暂存区的 git 命令。

AGENTS.md「多个代理并行」要求只提交自己的改动、`git add` 写明确路径；`progress/` 下还有
使用者的照片。这条规则原本只靠代理自觉，这里把它变成确定执行的门禁。

拦的是「不点名文件就批量收」的写法：
  git add . / -A / --all / -u / --update / :/ / *，以及参数是一个目录
  git commit -a / --all / -am（会顺带提交工作区里所有已跟踪文件的改动）
明确列出文件路径的 `git add a.py b.ts` 照常放行。

退出码 2 = 阻止该次工具调用，stderr 回传给代理作为理由；其他情况一律放行（解析失败也放行，
门禁不能反过来卡住正常工作）。
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

# 命令串里的分段符：&&、||、;、|、换行。引号内的不会出现在这些位置之外的概率很低，
# 误切只会让某段解析失败而放行，不会误拦。
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")

BULK_ADD_FLAGS = {"-A", "--all", "-u", "--update", "--no-ignore-removal"}
BULK_PATHSPECS = {".", "./", "*", ":/", ":(top)", ":/*", "-"}


def tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return []


def git_subcommand(argv: list[str]) -> tuple[str | None, list[str], str | None]:
    """返回 (子命令, 子命令参数, -C 指定的目录)。跳过 git 的全局选项。"""
    i = 1
    chdir = None
    while i < len(argv):
        a = argv[i]
        if a == "-C" and i + 1 < len(argv):
            chdir = argv[i + 1]
            i += 2
        elif a in ("-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(argv):
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            return a, argv[i + 1 :], chdir
    return None, [], chdir


def check_add(args: list[str], base: str) -> str | None:
    # 预览不改暂存区，正好是确认目录里有什么的手段，放行
    if "-n" in args or "--dry-run" in args:
        return None
    paths: list[str] = []
    after_dashdash = False
    for a in args:
        if not after_dashdash and a == "--":
            after_dashdash = True
            continue
        if not after_dashdash and a.startswith("-"):
            if a in BULK_ADD_FLAGS:
                return f"`git add {a}` 会收进工作区里所有改动"
            # 短选项合写，如 -Av
            if re.fullmatch(r"-[A-Za-z]+", a) and ("A" in a or "u" in a):
                return f"`git add {a}` 含 -A/-u，会收进工作区里所有改动"
            continue
        paths.append(a)

    for p in paths:
        if p in BULK_PATHSPECS or p.rstrip("/\\") in ("", "."):
            return f"`git add {p}` 会收进整个工作区"
        if any(ch in p for ch in "*?["):
            return f"`git add {p}` 是通配符，可能卷进别人的文件"
        if os.path.isdir(resolve(base, p)):
            return f"`git add {p}` 的参数是目录，会收进目录下所有改动"
    return None


def check_commit(args: list[str]) -> str | None:
    for a in args:
        if a == "--":
            break
        if a == "--all":
            return "`git commit --all` 会顺带提交所有已跟踪文件的改动"
        # -a、-am、-av 等短选项合写；-m 之后的值是消息，不在这里（消息作为独立 token）
        if re.fullmatch(r"-[A-Za-z]+", a) and "a" in a and not a.startswith("-m"):
            return f"`git commit {a}` 含 -a，会顺带提交所有已跟踪文件的改动"
    return None


MSYS_DRIVE = re.compile(r"^/([A-Za-z])(/|$)")


def native_path(p: str) -> str:
    """Git Bash 的 /c/Users/... 在 Windows 上要换成 C:/Users/...，否则会被当成
    当前盘根下的 C:\\c\\Users，目录判断全部落空。"""
    p = os.path.expanduser(p)
    if os.name == "nt":
        p = MSYS_DRIVE.sub(lambda m: f"{m.group(1)}:/", p)
    return p


def resolve(base: str, p: str) -> str:
    p = native_path(p)
    return p if os.path.isabs(p) else os.path.join(base, p)


def scan(command: str, cwd: str) -> str | None:
    base = cwd
    for seg in SEGMENT_SPLIT.split(command):
        argv = tokens(seg.strip())
        if not argv:
            continue
        # 跟踪 `cd x && git add .` 这种写法，让目录判断以正确的工作目录为准
        if argv[0] in ("cd", "Set-Location", "pushd") and len(argv) > 1:
            target = resolve(base, argv[1])
            # 解析不出来就留在原处：宁可按旧目录判断，也不能让后面的目录判断全部落空
            if os.path.isdir(target):
                base = target
            continue
        if os.path.basename(argv[0]).lower() not in ("git", "git.exe"):
            continue
        sub, rest, chdir = git_subcommand(argv)
        here = base if chdir is None else resolve(base, chdir)
        if sub in ("add", "stage"):
            reason = check_add(rest, here)
        elif sub == "commit":
            reason = check_commit(rest)
        else:
            reason = None
        if reason:
            return reason
    return None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read())
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return 0
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    reason = scan(command, cwd)
    if reason is None:
        return 0
    message = (
        f"已拦截：{reason}。\n"
        "Athena 规则（AGENTS.md「多个代理并行」）：只提交自己的改动，git add 写明确的文件路径，"
        "不整目录添加——工作区里可能有其他代理的半成品，progress/ 下有使用者的照片。\n"
        "请改为逐个列出文件；不确定目录里有哪些改动时先跑 `git status --porcelain <目录>`。\n"
    )
    # Windows 上 stderr 默认走系统代码页（中文环境是 GBK），而 Claude Code 按 UTF-8 读
    sys.stderr.buffer.write(message.encode("utf-8"))
    sys.stderr.flush()
    return 2


if __name__ == "__main__":
    sys.exit(main())
