"""Keep the project off the SVG rendering path, and off empty image widgets.

ADR 0038：插图不再是 SVG 图片。原因不只是"载体选错"，还有一条很实际的：
`Gtk::Picture` 显示图片要经 `GdkTexture`，它只内建 PNG/JPEG/TIFF，SVG 一律
回退到 gdk-pixbuf 的外部 loader（librsvg）。那个 loader 缺失时，GTK 既不报错
也不显示——页面上只剩一块留着高度的空白，排查要一路查到 pixbuf 的 loaders
缓存。GTK 4.20+ 确实内建了 SVG 解析器，但它只服务图标路径，且 Ubuntu LTS 的
GTK 还没有，跨平台不能依赖。

所以这里守三件事：不再出现 SVG 资源、不再引用已废弃的插图目录、`.blp` 里的
`Picture` 都要有人填资源（声明了没人填同样是一块静默的空白）。
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import ProjectError

# 运行时会被加载的资源目录。图标是 PNG 尺寸集，其余资源不该再有 SVG。
RESOURCE_DIR = Path("resources")
# 已废弃的插图目录（ADR 0034 删手册、ADR 0038 删插图之后彻底空了）。
RETIRED_PREFIX = "/app/articles/"

SOURCE_DIRS = ("ui", "render", "practice", "registry")

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
    """Reject SVG resources, retired figure paths and unfilled Pictures."""
    sources = _source_text(root)

    # 1. 资源目录里不再放 SVG：它要外部解码器，缺了就是一块静默的空白。
    resource_root = root / RESOURCE_DIR
    if resource_root.is_dir():
        for path in sorted(resource_root.rglob("*.svg")):
            raise ProjectError(
                f"{path.relative_to(root)} is an SVG resource; ADR 0038 已经把插图"
                "迁到 .blp 控件与 Cairo 自绘，图标改用 PNG 尺寸集——"
                "SVG 要经外部解码器，缺 loader 时只会显示空白"
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
