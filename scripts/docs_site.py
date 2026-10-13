#!/usr/bin/env python3
"""把仓库里的文档构建成静态站点，发布到 GitHub Pages（ADR 0154）。

站点没有自己的内容：源是 `docs/`（含全部 ADR）加根目录的 README / AGENTS / CHANGELOG，
先按原目录结构暂存到 `.cache/docs-site/src`，再交给 MkDocs Material 渲染。
这样站点永远等于仓库里的文档，没有第二份要同步。

暂存时做两件事，否则站点会出现大片死链和吞字：

1. 指向暂存范围之外的相对链接（应用目录、源码文件）改写成 GitHub 上的绝对地址。
2. 文中的 `<id>` 这类裸尖括号会被当成未知 HTML 标签吞掉，转义成文字。

用法：
    python3 scripts/docs_site.py           # 构建到 .cache/docs-site/site
    python3 scripts/docs_site.py --serve   # 本地预览（热重载）
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_SRC = REPO_ROOT / "scripts" / "docs-site" / "mkdocs.yml"
STAGE = REPO_ROOT / ".cache" / "docs-site"
CONTENT = STAGE / "src"

GITHUB = "https://github.com/iguoya/Athena"
BRANCH = "main"

# 进站点的内容：目录整体带上（含 ADR 引用的图片），再加三份根文档。
INCLUDE_DIRS = ("docs",)
INCLUDE_FILES = ("README.md", "AGENTS.md", "CHANGELOG.md")

# 在线演示：站点 /demo/<名字>/ 下放纯前端应用的 Vite 构建产物（ADR 0154）。
# 只收不依赖 Tauri 后端就能在浏览器里跑的应用；产物由 pages.yml 先构建，本地没构建
# 就跳过，不影响文档站本身。
DEMOS = {"earth": "practice/earth/dist"}

# 这些是文档里真会用到的 HTML 标签，其余尖括号一律当文字。
KNOWN_HTML = {
    "a", "b", "i", "em", "strong", "code", "pre", "p", "br", "hr", "div", "span",
    "details", "summary", "kbd", "sup", "sub", "mark", "del", "ins", "small",
    "img", "table", "thead", "tbody", "tr", "th", "td", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "picture", "source",
}

LINK_RE = re.compile(r"(\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
TAG_RE = re.compile(r"<(/?)([A-Za-z][\w-]*)([^<>]*)>")


def stage_content() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    CONTENT.mkdir(parents=True)
    for name in INCLUDE_DIRS:
        shutil.copytree(REPO_ROOT / name, CONTENT / name)
    for name in INCLUDE_FILES:
        shutil.copy2(REPO_ROOT / name, CONTENT / name)
    shutil.copy2(CONFIG_SRC, STAGE / "mkdocs.yml")

    for md in sorted(CONTENT.rglob("*.md")):
        origin = REPO_ROOT / md.relative_to(CONTENT)
        text = md.read_text(encoding="utf-8")
        md.write_text(transform(text, origin.parent), encoding="utf-8")


def transform(text: str, origin_dir: Path) -> str:
    out: list[str] = []
    fence: str | None = None
    for line in text.split("\n"):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in ("```", "~~~"):
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            out.append(line)
            continue
        if fence is not None:
            out.append(line)
            continue
        line = LINK_RE.sub(lambda m: m.group(1) + rewrite_target(m.group(2), origin_dir) + m.group(3), line)
        out.append(escape_stray_tags(line))
    return "\n".join(out)


def rewrite_target(target: str, origin_dir: Path) -> str:
    """暂存范围内的链接原样保留，范围外但真实存在的改成 GitHub 地址。"""
    if re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*:|#|/)", target):
        return target
    path_part, sep, anchor = target.partition("#")
    if not path_part:
        return target
    resolved = (origin_dir / path_part).resolve()
    try:
        rel = resolved.relative_to(REPO_ROOT)
    except ValueError:
        return target
    staged_path = CONTENT / rel
    if staged_path.is_dir() and (staged_path / "README.md").exists():
        # 指向目录的链接落到目录自己的 README，站点里目录本身没有页面。
        return f"{path_part.rstrip('/')}/README.md{sep}{anchor}"
    if staged_path.exists() or not resolved.exists():
        return target
    kind = "tree" if resolved.is_dir() else "blob"
    return f"{GITHUB}/{kind}/{BRANCH}/{rel.as_posix()}{sep}{anchor}"


def escape_stray_tags(line: str) -> str:
    """行内代码以外的 `<foo>` 若不是已知 HTML 标签或自动链接，转义成文字。"""
    pieces: list[str] = []
    last = 0
    for code in INLINE_CODE_RE.finditer(line):
        pieces.append(_escape(line[last:code.start()]))
        pieces.append(code.group(0))
        last = code.end()
    pieces.append(_escape(line[last:]))
    return "".join(pieces)


def _escape(segment: str) -> str:
    def repl(m: re.Match[str]) -> str:
        name, rest = m.group(2), m.group(3)
        if name.lower() in KNOWN_HTML:
            return m.group(0)
        # 自动链接 <https://…> / <mailto:…>
        if re.match(r"^[:/]", rest) or "@" in name + rest:
            return m.group(0)
        return m.group(0).replace("<", "&lt;").replace(">", "&gt;")

    return TAG_RE.sub(repl, segment)


def run_mkdocs(serve: bool) -> int:
    try:
        import mkdocs  # noqa: F401
    except ImportError:
        raise SystemExit(
            "缺 MkDocs Material，安装：\n"
            "  python3 -m pip install -r scripts/docs-site/requirements.txt"
        )
    command = "serve" if serve else "build"
    return subprocess.call(
        [sys.executable, "-m", "mkdocs", command, "-f", str(STAGE / "mkdocs.yml")],
        cwd=STAGE,
    )


def copy_demos() -> None:
    site = STAGE / "site"
    for name, built in DEMOS.items():
        source = REPO_ROOT / built
        if not source.is_dir():
            print(f"跳过演示 {name}：没有构建产物 {built}（先构建该应用的前端）")
            continue
        shutil.copytree(source, site / "demo" / name)
        print(f"已加入演示 {name} → /demo/{name}/")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--serve", action="store_true", help="本地预览")
    args = parser.parse_args()
    stage_content()
    code = run_mkdocs(args.serve)
    if code == 0 and not args.serve:
        copy_demos()
    raise SystemExit(code)


if __name__ == "__main__":
    main()
