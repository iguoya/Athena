"""Render GResource XML and expose Blueprint build entries.

`.blp` 的清单只在这里算一次，Meson 编译和 GResource 打包都用它，不再有第二份
手写名单：

- 章节页的 `.blp` 由 `athena.json` 决定（`model["ui"]`），发布到 `/app/chapters/`；
- 共享的 `.blp` 是 `resources/ui/` 顶层的全部 `.blp`，减去已被章节引用的那些
  （例如数据驱动页面用的 `lesson.blp`），发布到 `/app/<名字>.ui`。

新增一个共享 `.blp` 只需把文件放进 `resources/ui/`。
"""

from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from .model import ProjectError

SHARED_BLUEPRINT_DIR = Path("resources") / "ui"


def shared_blueprints(model: dict, root: Path) -> list[str]:
    """`resources/ui/` 顶层、没被任何章节引用的 `.blp`，按路径排序。"""
    ui_dir = root / SHARED_BLUEPRINT_DIR
    if not ui_dir.is_dir():
        return []
    chapter_blueprints = set(model["ui"].values())
    return [
        blueprint
        for blueprint in (
            path.relative_to(root).as_posix() for path in sorted(ui_dir.glob("*.blp"))
        )
        if blueprint not in chapter_blueprints
    ]


def blueprint_entries(model: dict, root: Path) -> list[tuple[str, str, str]]:
    """每个要编译的 `.blp`：(Meson 目标名, 源路径, 产物 .ui 文件名)。

    所有 `.ui` 产物落在同一个构建目录，重名会互相覆盖，所以这里直接拒绝。
    """
    entries = [
        (Path(ui_name).stem, blueprint, ui_name)
        for ui_name, blueprint in sorted(model["ui"].items())
    ]
    owners = {ui_name: blueprint for _, blueprint, ui_name in entries}
    for blueprint in shared_blueprints(model, root):
        ui_name = Path(blueprint).with_suffix(".ui").name
        if ui_name in owners:
            raise ProjectError(
                f"blueprints {owners[ui_name]!r} and {blueprint!r} both generate "
                f"{ui_name!r}; rename one of them"
            )
        owners[ui_name] = blueprint
        entries.append((Path(ui_name).stem, blueprint, ui_name))
    return entries


def render_resources(model: dict, root: Path) -> str:
    # ADR 0034 之后 resources/articles/ 下不再有 Markdown 手册，只剩原生学习页
    # 引用的插图。路径相对 resources/ 而不是项目根：GResource 的 prefix 是 /app，
    # 全仓库约定是 /app/<类别>/...（见 ui/icon_utils.cc 的同款前缀转换），学习页
    # 按 /app/articles/cpp/images/xxx.svg 取图。写成 resources/articles/... 也能
    # 编译通过（source_dir 含项目根），但会发布到 /app/resources/... 而加载不到。
    articles_dir = root / "resources" / "articles"
    article_assets = [
        path.relative_to(root / "resources").as_posix()
        for path in sorted(articles_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() not in {".md", ".markdown"}
    ] if articles_dir.is_dir() else []
    article_entries = [
        f'    <file compressed="true">{xml_escape(asset)}</file>'
        for asset in article_assets
    ]
    ui_entries = [
        f'    <file compressed="true">{xml_escape(ui_name)}</file>'
        for ui_name in sorted(model["ui"])
    ]
    source_entries = [
        f'    <file compressed="true">{xml_escape(source)}</file>'
        for source in sorted(model["source_files"])
    ]
    # 可编辑骨架案例（ADR 0053）。用 alias 去掉 cases/ 前缀，发布成
    # /app/cases/<case>/<file>；运行期按这个路径把骨架展开成工作副本。
    case_entries = [
        '    <file alias="{}" compressed="true">{}</file>'.format(
            xml_escape(asset.split("/", 1)[1]),
            xml_escape(asset),
        )
        for asset in sorted(model["case_files"])
    ]
    # 学习页内容（ADR 0055）。alias 去掉 lessons/ 前缀，发布成
    # /app/lessons/<章节 ID>.json，运行期按章节 ID 直接取。
    lesson_entries = [
        '    <file alias="{}" compressed="true">{}</file>'.format(
            xml_escape(asset.split("/", 1)[1]),
            xml_escape(asset),
        )
        for asset in sorted(model["lesson_files"])
    ]
    icon_entries = []
    icons_dir = root / "resources" / "icons"
    if icons_dir.is_dir():
        icon_entries = [
            "    <file alias=\"{}\">{}</file>".format(
                xml_escape(path.relative_to(icons_dir).as_posix()),
                xml_escape(path.relative_to(root / "resources").as_posix()),
            )
            for path in sorted(icons_dir.rglob("*"))
            if path.is_file() and not any(part.startswith(".") for part in path.parts)
        ]

    shared_ui_entries = [
        '    <file preprocess="xml-stripblanks">{}</file>'.format(
            xml_escape(Path(blueprint).with_suffix(".ui").name)
        )
        for blueprint in shared_blueprints(model, root)
    ]

    def entries_or_comment(entries: list[str], comment: str) -> str:
        return "\n".join(entries) if entries else f"    <!-- {comment} -->"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/app">
{entries_or_comment(shared_ui_entries, "暂无共享界面")}
    <file>style.css</file>
{entries_or_comment(article_entries, "暂无文章")}
  </gresource>
  <gresource prefix="/app/chapters">
{entries_or_comment(ui_entries, "暂无章节")}
  </gresource>
  <gresource prefix="/app/data">
    <file alias="chapter_catalog.json" compressed="true">chapter_catalog.generated.json</file>
  </gresource>
  <gresource prefix="/app/sources">
{entries_or_comment(source_entries, "暂无教学源码")}
  </gresource>
  <gresource prefix="/app/lessons">
{entries_or_comment(lesson_entries, "暂无学习页内容")}
  </gresource>
  <gresource prefix="/app/cases">
{entries_or_comment(case_entries, "暂无实验案例")}
  </gresource>
  <gresource prefix="/app/icons">
{entries_or_comment(icon_entries, "暂无图标")}
  </gresource>
</gresources>
'''
