"""Keep figures off the external-decoder path, and off empty image widgets.

ADR 0038：插图优先用 `.blp` 控件与 Cairo 自绘承载。这里守的不是"仓库里不许有
SVG"，而是**不许把 SVG 交给需要外部解码器的那条路**——`Gtk::Picture` /
`Gdk::Texture` 内部走 `gdk_texture_new_from_*`，它只内建 PNG/JPEG/TIFF，SVG
一律回退到 gdk-pixbuf 的 loader（librsvg）。那个 loader 缺失时 GTK 既不报错也
不显示，页面上只剩一块留着高度的空白。

SVG 本身没有被禁掉：GTK 4.20 起内建了 SVG 解析器，走的是**图标路径**
（`GtkIconPaintable` / icon theme，可用 `Gtk::IconTheme::add_resource_path()`
把 GResource 里的图标目录挂进去），那条路不依赖 librsvg。确有需要时可以走它，
代价是要求 GTK ≥ 4.20，并且受图标路径的尺寸与着色语义约束。
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import ProjectError

# 运行时会被加载的资源目录。当前的应用图标是 PNG 尺寸集。
RESOURCE_DIR = Path("resources")
# 已废弃的插图目录（ADR 0034 删手册、ADR 0038 删插图之后彻底空了）。
RETIRED_PREFIX = "/app/articles/"

SOURCE_DIRS = ("ui", "render", "practice", "registry")

_PICTURE = re.compile(r"^\s*Picture\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", re.MULTILINE)
# set_resource("....svg") / create_from_resource("....svg") / set_filename(...)
_TEXTURE_SVG = re.compile(
    r'(?:set_resource|set_filename|set_file|create_from_resource'
    r'|create_from_filename|create_from_file)\s*\(\s*"[^"]+\.svg"')


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
    """Reject decoder-dependent SVG use, retired paths and unfilled Pictures."""
    sources = _source_text(root)

    # 1. 不许把 SVG 交给 Picture / Texture：那条路要外部解码器，缺了就是一块
    #    静默的空白。SVG 走 GTK 内建解析器的图标路径则不在此限。
    for match in _TEXTURE_SVG.finditer(sources):
        raise ProjectError(
            f"{match.group(0)} hands an SVG to Gtk::Picture/Gdk::Texture; "
            "那条路要 gdk-pixbuf 的外部 SVG loader，缺了只会显示空白。"
            "按 ADR 0038 改用 .blp 控件或 Cairo 自绘；确需 SVG 时走 GTK 内建"
            "解析器的图标路径（IconTheme::add_resource_path + icon-name）"
        )

    # 2. 不再引用已废弃的插图目录。
    if RETIRED_PREFIX in sources:
        raise ProjectError(
            f"page code still references {RETIRED_PREFIX}; 那批插图已按 ADR 0038 "
            "改成控件与自绘，引用应当一起删掉"
        )

    # 3. `.blp` 里声明的每个 Picture 都要有人给它设资源（PNG 同样适用）。
    blueprint_root = root / RESOURCE_DIR / "ui"
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
