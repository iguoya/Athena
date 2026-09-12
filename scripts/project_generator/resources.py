"""Render GResource XML and expose Blueprint build entries."""

from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


def blueprint_entries(model: dict) -> list[tuple[str, str, str]]:
    return [
        (Path(ui_name).stem, blueprint, ui_name)
        for ui_name, blueprint in sorted(model["ui"].items())
    ]


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

    def entries_or_comment(entries: list[str], comment: str) -> str:
        return "\n".join(entries) if entries else f"    <!-- {comment} -->"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/app">
    <file preprocess="xml-stripblanks">window.ui</file>
    <file preprocess="xml-stripblanks">learning_unit.ui</file>
    <file preprocess="xml-stripblanks">checkpoint.ui</file>
    <file>style.css</file>
    <file>backdrop.svg</file>
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
  <gresource prefix="/app/icons">
{entries_or_comment(icon_entries, "暂无图标")}
  </gresource>
</gresources>
'''
