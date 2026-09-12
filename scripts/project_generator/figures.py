"""Keep lesson figures, the widgets that show them and the files on disk in sync.

学习页的插图有三段链路：`.blp` 里声明一个 `Picture` 控件、页面代码给它
`set_resource("/app/articles/...")`、`resources/articles/` 下真的有那个文件。
任何一段断掉，GTK 都不会报错，只是画一块空白——界面上看起来就是"图没了"。
这里把三段对起来，让断链在 `scripts/check.sh` 阶段就失败。

它查不到的是第四种断链：运行环境缺 gdk-pixbuf 的 SVG loader（librsvg），
那时所有图一起变空白。那条由 tests/gtk_resource_test.cc 真解码一遍来守。
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import ProjectError

# 插图与引用它的资源前缀。两者必须一起改。
FIGURE_DIR = Path("resources") / "articles"
RESOURCE_PREFIX = "/app/articles/"

# 页面代码所在的目录：只有这些算"用上了"。测试里出现的路径不算，
# 否则删掉最后一处真实用法也不会被发现。
SOURCE_DIRS = ("ui", "render", "practice")

_REFERENCE = re.compile(r'"' + re.escape(RESOURCE_PREFIX) + r'([^"]+)"')
_PICTURE = re.compile(r"^\s*Picture\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", re.MULTILINE)


def _source_text(root: Path) -> str:
    parts: list[str] = []
    for directory in SOURCE_DIRS:
        source_root = root / directory
        if not source_root.is_dir():
            continue
        for path in sorted(source_root.rglob("*.cc")):
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def check_figures(root: Path) -> None:
    """Validate every figure reference, widget and file. Raises ProjectError."""
    sources = _source_text(root)
    referenced = set(_REFERENCE.findall(sources))

    # 1. 引用的图必须真的在仓库里，否则运行时是一块空白。
    for relative in sorted(referenced):
        if not (root / FIGURE_DIR / relative).is_file():
            raise ProjectError(
                f"lesson figure {RESOURCE_PREFIX}{relative} is referenced by page "
                f"code but {FIGURE_DIR / relative} does not exist"
            )

    # 2. `.blp` 里声明的每个 Picture 都要有人给它设资源。声明了却没人填，
    #    页面上就是一块留着高度的空白，且不会有任何诊断。
    blueprint_root = root / "resources" / "ui"
    if blueprint_root.is_dir():
        for blueprint in sorted(blueprint_root.rglob("*.blp")):
            text = blueprint.read_text(encoding="utf-8")
            for widget_id in _PICTURE.findall(text):
                if f'"{widget_id}"' not in sources:
                    raise ProjectError(
                        f"{blueprint.relative_to(root)} declares Picture "
                        f"{widget_id} but no page code sets its resource; "
                        "add it to the figure table or drop the widget"
                    )

    # 3. 反过来，目录里不留没人引用的图：它们会被打进 GResource，又和页面
    #    讲法各说各话——ADR 0034 删掉 Markdown 手册后留下的那批就是这样。
    figure_root = root / FIGURE_DIR
    if figure_root.is_dir():
        for path in sorted(figure_root.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            relative = path.relative_to(figure_root).as_posix()
            if relative not in referenced:
                raise ProjectError(
                    f"{FIGURE_DIR / relative} is not referenced by any page; "
                    "reference it from a lesson or delete it"
                )
