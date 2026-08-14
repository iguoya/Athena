"""Render GResource XML and expose Blueprint build entries."""

from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


def blueprint_entries(model: dict) -> list[tuple[str, str, str]]:
    return [
        (Path(ui_name).stem, blueprint, ui_name)
        for ui_name, blueprint in sorted(model["ui"].items())
    ]


def render_resources(model: dict, root: Path) -> str:
    article_entries = [
        f'    <file compressed="true">{xml_escape(document)}</file>'
        for document in sorted(model["documents"])
    ]
    ui_entries = [
        f'    <file compressed="true">{xml_escape(ui_name)}</file>'
        for ui_name in sorted(model["ui"])
    ]
    icon_entries = []
    icons_dir = root / "resources" / "icons"
    if icons_dir.is_dir():
        icon_entries = [
            f"    <file>{xml_escape(path.relative_to(root / 'resources').as_posix())}</file>"
            for path in sorted(icons_dir.rglob("*"))
            if path.is_file() and not any(part.startswith(".") for part in path.parts)
        ]

    def entries_or_comment(entries: list[str], comment: str) -> str:
        return "\n".join(entries) if entries else f"    <!-- {comment} -->"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/app">
    <file preprocess="xml-stripblanks">window.ui</file>
    <file>style.css</file>
    <file>article.css</file>
{entries_or_comment(article_entries, "暂无文章")}
  </gresource>
  <gresource prefix="/app/chapters">
{entries_or_comment(ui_entries, "暂无章节")}
  </gresource>
  <gresource prefix="/app/data">
    <file compressed="true">athena.json</file>
  </gresource>
  <gresource prefix="/app/icons">
{entries_or_comment(icon_entries, "暂无图标")}
  </gresource>
</gresources>
'''
