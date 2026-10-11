#!/usr/bin/env python3
"""抽出或补全 CHANGELOG 中某一版的发版说明。

优先用手写的 ``## [VERSION]`` 节。若缺失或正文为空，则统计上一版标签
（或上一节版本）到 HEAD 之间的提交，按 Keep a Changelog 风格生成一节，
并可写回 CHANGELOG.md。

用法：
  python3 scripts/changelog_notes.py 7.0.0
  python3 scripts/changelog_notes.py 7.0.0 CHANGELOG.md
  python3 scripts/changelog_notes.py 7.0.0 --write          # 缺节时写回文件
  python3 scripts/changelog_notes.py 7.0.0 --from-git       # 强制用提交生成
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path


SECTION_RE = re.compile(
    r"^## \[(\d+\.\d+\.\d+)\][^\n]*\n(.*?)(?=^## |\Z)",
    flags=re.MULTILINE | re.DOTALL,
)


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise SystemExit(f"git {' '.join(args)} 失败：{err}")
    return result.stdout


def parse_version(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise SystemExit(f"版本号必须是 MAJOR.MINOR.PATCH，收到：{version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def extract_section(changelog: str, version: str) -> str | None:
    pattern = rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, changelog, flags=re.MULTILINE | re.DOTALL)
    if match is None:
        return None
    # 最后一节会连带文末的版本对比链接定义（[X.Y.Z]: url），它们属于整份文件。
    body = re.sub(r"^\[\d+\.\d+\.\d+\]:[ \t]+\S+[ \t]*$", "", match.group(1), flags=re.MULTILINE)
    body = body.strip()
    return body + "\n" if body else None


def versions_in_changelog(changelog: str) -> list[str]:
    return [m.group(1) for m in SECTION_RE.finditer(changelog)]


def previous_version(changelog: str, version: str) -> str | None:
    target = parse_version(version)
    older = []
    for item in versions_in_changelog(changelog):
        parsed = parse_version(item)
        if parsed < target:
            older.append((parsed, item))
    if not older:
        return None
    older.sort()
    return older[-1][1]


def previous_git_tag(repo: Path, version: str) -> str | None:
    raw = run_git(["tag", "-l", "v*.*.*"], repo)
    target = parse_version(version)
    older: list[tuple[tuple[int, int, int], str]] = []
    for line in raw.splitlines():
        tag = line.strip()
        if not tag.startswith("v"):
            continue
        ver = tag[1:]
        try:
            parsed = parse_version(ver)
        except SystemExit:
            continue
        if parsed < target:
            older.append((parsed, tag))
    if not older:
        return None
    older.sort()
    return older[-1][1]


def classify_subject(subject: str) -> str:
    lower = subject.lower()
    if lower.startswith(("fix", "bugfix")) or subject.startswith(("修复", "修正")):
        return "修复"
    if lower.startswith(("feat", "add")) or subject.startswith(("新增", "添加")):
        return "新增"
    if lower.startswith(("docs", "doc")) or subject.startswith("文档"):
        return "文档"
    if lower.startswith(("test", "ci", "chore", "build", "release")):
        return "杂项"
    return "变更"


def collect_commits(repo: Path, since_ref: str | None) -> list[str]:
    # %B 全文；用 \x1e 分隔提交，避免 subject 里的换行搅乱列表。
    range_spec = f"{since_ref}..HEAD" if since_ref else "HEAD"
    raw = run_git(
        [
            "log",
            range_spec,
            "--no-merges",
            "--pretty=format:%s%x1e",
        ],
        repo,
    )
    subjects: list[str] = []
    for chunk in raw.split("\x1e"):
        subject = chunk.strip().splitlines()[0].strip() if chunk.strip() else ""
        if not subject:
            continue
        # 跳过纯发版杂务，避免把「release: x.y.z」再写进说明循环引用。
        if re.match(r"^release:\s*\d+\.\d+\.\d+", subject, flags=re.I):
            continue
        subjects.append(subject)
    return subjects


def render_from_commits(version: str, subjects: list[str], since_label: str) -> str:
    today = date.today().isoformat()
    if not subjects:
        body = (
            f"## [{version}] - {today}\n\n"
            f"### 变更\n\n"
            f"- （自 {since_label} 起无新的非合并提交）\n"
        )
        return body

    buckets: dict[str, list[str]] = {
        "变更": [],
        "新增": [],
        "修复": [],
        "文档": [],
        "杂项": [],
    }
    for subject in subjects:
        buckets[classify_subject(subject)].append(subject)

    lines = [
        f"## [{version}] - {today}",
        "",
        f"_以下由发版脚本根据 `{since_label}..HEAD` 的提交自动汇总；"
        "可再手工改写成更可读的说明。_",
        "",
    ]
    for heading in ("变更", "新增", "修复", "文档", "杂项"):
        items = buckets[heading]
        if not items:
            continue
        lines.append(f"### {heading}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_section(
    version: str,
    changelog_path: Path,
    repo: Path,
    force_from_git: bool,
) -> tuple[str, bool]:
    """返回 (完整 ## 节或仅正文, 是否由 git 生成)。

    手写节只返回正文（无标题）；git 生成返回带 ``## [ver]`` 的完整节，
    方便 --write 插入。stdout 给 Release 时统一成「正文」。
    """
    text = changelog_path.read_text(encoding="utf-8")
    if not force_from_git:
        body = extract_section(text, version)
        if body is not None:
            return body, False

    prev_tag = previous_git_tag(repo, version)
    prev_ver = previous_version(text, version)
    since_ref = prev_tag
    since_label = prev_tag or (f"v{prev_ver}" if prev_ver else "仓库起点")
    if since_ref is None and prev_ver is not None:
        # CHANGELOG 有上一版但本地可能没有对应 tag 时，仍尽量用 tag 名试一次。
        candidate = f"v{prev_ver}"
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            since_ref = candidate
            since_label = candidate

    subjects = collect_commits(repo, since_ref)
    full = render_from_commits(version, subjects, since_label)
    return full, True


def insert_section(changelog: str, full_section: str) -> str:
    """把完整 ``## [ver]`` 节插到文件头说明之后、第一节之前。"""
    if SECTION_RE.search(changelog):
        return SECTION_RE.sub(lambda m: full_section + "\n" + m.group(0), changelog, count=1)
    # 尚无任何版本节：接在文末。
    return changelog.rstrip() + "\n\n" + full_section + "\n"


def notes_body(section: str, from_git: bool) -> str:
    """Release 正文：若是完整节则去掉标题行，只留 ### 以下。"""
    if from_git:
        lines = section.splitlines()
        # 丢掉 ## [x.y.z] - date
        if lines and lines[0].startswith("## ["):
            rest = "\n".join(lines[1:]).lstrip("\n")
            return rest if rest.endswith("\n") else rest + "\n"
    return section if section.endswith("\n") else section + "\n"


# 新块的起点：标题、列表项、引用、表格、围栏、分隔线。
BLOCK_START_RE = re.compile(r"^(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```|~~~|(?:[-*_]\s*){3,}$)")


def _is_wide(ch: str) -> bool:
    return unicodedata.east_asian_width(ch) in ("W", "F")


def unwrap_for_release(text: str) -> str:
    """把段落与列表项里的手动折行接回一行。

    CHANGELOG.md 按约 80 列折行，仓库里渲染文件时单个换行会被合并；
    但 GitHub 的 Release 正文把单个换行当 <br>，原样贴进去每行都会
    在源码折行处断开。接行规则与浏览器渲染一致：两侧都是中日韩宽
    字符时直接拼接，否则补一个空格。围栏代码块内原样保留。
    """
    out: list[str] = []
    in_fence = False
    joinable = False  # 上一行是否为可被续接的段落或列表项文本
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            out.append(line)
            joinable = False
            continue
        if in_fence or not stripped:
            out.append(line)
            joinable = False
            continue
        is_block_start = BLOCK_START_RE.match(stripped) is not None
        prev = out[-1] if out else ""
        hard_break = prev.endswith(("  ", "\\"))
        if joinable and not is_block_start and not hard_break:
            sep = "" if _is_wide(prev.rstrip()[-1]) and _is_wide(stripped[0]) else " "
            out[-1] = prev.rstrip() + sep + stripped
            continue
        out.append(line)
        # 标题、表格、分隔线自成一行，后面的行不往上接。
        joinable = not (is_block_start and not re.match(r"^([-*+]|\d+[.)])\s", stripped))
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="MAJOR.MINOR.PATCH")
    parser.add_argument(
        "changelog",
        nargs="?",
        default="CHANGELOG.md",
        help="CHANGELOG 路径（默认当前目录 CHANGELOG.md）",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="缺节时把自动汇总写回 CHANGELOG.md",
    )
    parser.add_argument(
        "--from-git",
        action="store_true",
        help="忽略已有手写节，强制按提交重新生成",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="git 仓库根（默认从 CHANGELOG 位置向上找）",
    )
    args = parser.parse_args(argv[1:])

    parse_version(args.version)
    changelog_path = Path(args.changelog).resolve()
    if not changelog_path.is_file():
        raise SystemExit(f"找不到 {changelog_path}")

    repo = Path(args.repo).resolve() if args.repo else changelog_path.parent
    # subjects/cpp/CHANGELOG.md → 仓库根在上两级
    if not (repo / ".git").exists() and (repo.parent.parent / ".git").exists():
        repo = repo.parent.parent
    if not (repo / ".git").exists():
        # CI checkout 可能只有 .git 文件指向；rev-parse 更稳
        probe = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            repo = Path(probe.stdout.strip())
        else:
            raise SystemExit(f"在 {repo} 找不到 git 仓库")

    section, from_git = build_section(
        args.version, changelog_path, repo, force_from_git=args.from_git
    )

    if from_git and args.write:
        text = changelog_path.read_text(encoding="utf-8")
        if extract_section(text, args.version) is None or args.from_git:
            if args.from_git and extract_section(text, args.version) is not None:
                # 替换已有节
                text = re.sub(
                    rf"^## \[{re.escape(args.version)}\][^\n]*\n.*?(?=^## |\Z)",
                    section + ("\n" if not section.endswith("\n") else ""),
                    text,
                    count=1,
                    flags=re.MULTILINE | re.DOTALL,
                )
            else:
                text = insert_section(text, section)
            changelog_path.write_text(text, encoding="utf-8")
            print(f"已写入 {changelog_path} 的 ## [{args.version}] 节", file=sys.stderr)

    if from_git:
        print(
            f"注意：## [{args.version}] 由提交自动汇总"
            f"（自上一版本标签起）。",
            file=sys.stderr,
        )

    # 正文要重定向进 release-notes.md；Windows 默认 GBK 编码、CRLF 换行，
    # 不固定就会乱码或报错，换行也会和后面追加的页脚混成两种。
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stdout.write(unwrap_for_release(notes_body(section, from_git)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
