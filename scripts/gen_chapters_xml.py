#!/usr/bin/env python3
"""从 chapters.json 读取章节定义，生成 gresource.xml。

stdout: 每行 "chapter_id|blp_relative_path|ui_filename" 供 meson 解析。
不再扫描文件系统——所有元数据以 chapters.json 为单一来源。
"""
import json
import os
import sys


CONTENT_TYPES = {"code", "article"}


def validate_project_path(path, label):
    if not isinstance(path, str) or not path:
        raise ValueError(f"{label} must be a non-empty string")
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if os.path.isabs(path) or ".." in parts or "." in parts:
        raise ValueError(f"{label} must be a safe project-relative path: {path!r}")
    return normalized


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: gen_chapters_xml.py <chapters.json> <project_root> <output_xml>",
            file=sys.stderr,
        )
        sys.exit(1)

    json_path = sys.argv[1]
    project_root = sys.argv[2]
    output_xml = sys.argv[3]

    with open(json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if config.get("schema") != 1:
        print(
            f"Error: unsupported chapters schema: {config.get('schema')!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        defaults = config["defaults"]
        default_content = defaults.get("content", "code")
        chapter_ui = defaults["chapter_ui"]
        default_blueprints = {
            content: chapter_ui[content]["blueprint"]
            for content in CONTENT_TYPES
        }
        categories = config["categories"]
    except (KeyError, TypeError, AttributeError):
        print("Error: invalid chapters.json root structure", file=sys.stderr)
        sys.exit(1)

    if default_content not in CONTENT_TYPES:
        print(
            f"Error: unsupported defaults.content: {default_content!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 新 schema: category -> chapter。普通章节使用默认 BLP，特殊章节可覆盖。
    chapters = []
    for category in categories:
        for chapter in category.get("chapters", []):
            chapter = dict(chapter)
            content = chapter.get("content", default_content)
            if content not in CONTENT_TYPES:
                print(
                    f"Error: chapter '{chapter.get('name', '')}' has unsupported "
                    f"content {content!r}",
                    file=sys.stderr,
                )
                sys.exit(1)

            custom_ui = chapter.get("ui", {})
            chapter["content"] = content
            chapter["ui_resource"] = custom_ui.get(
                "blueprint", default_blueprints[content]
            )
            if content == "article" and not custom_ui and not chapter.get("document"):
                print(
                    f"Error: article chapter '{chapter.get('name', '')}' "
                    "requires a document",
                    file=sys.stderr,
                )
                sys.exit(1)
            chapters.append(chapter)
    if not chapters:
        print("Warning: no chapters defined in chapters.json", file=sys.stderr)

    # 校验 blp 文件存在，并去重（多个章节可能共用同一个 .blp 模板）
    seen_ui = {}       # ui_name -> blp_file（去重 .ui 条目）
    article_documents = set()
    for ch in chapters:
        ch_id = ch.get("name", "")
        blp_file = ch.get("ui_resource", "")  # ui_resource 直接存 blp 路径

        if not blp_file:
            print(f"Warning: chapter '{ch_id}' has no ui_resource, skipping", file=sys.stderr)
            continue

        try:
            blp_file = validate_project_path(
                blp_file,
                f"chapter '{ch_id}' blueprint",
            )
        except ValueError as error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)

        blp_abs = os.path.join(project_root, blp_file)
        if not os.path.isfile(blp_abs):
            print(f"Error: blp file not found for chapter '{ch_id}': {blp_abs}", file=sys.stderr)
            sys.exit(1)

        # 从 blp 文件名派生 .ui 文件名: welcome.blp -> welcome.ui
        ui_name = os.path.basename(blp_file)[:-4] + ".ui"
        if ui_name not in seen_ui:
            seen_ui[ui_name] = blp_file

        document = ch.get("document", "")
        if document:
            try:
                document = validate_project_path(
                    document,
                    f"chapter '{ch_id}' document",
                )
            except ValueError as error:
                print(f"Error: {error}", file=sys.stderr)
                sys.exit(1)
            if not document.startswith("resources/articles/"):
                print(
                    f"Error: chapter '{ch_id}' document must be stored under "
                    f"resources/articles/: {document}",
                    file=sys.stderr,
                )
                sys.exit(1)
            document_abs = os.path.join(project_root, document)
            if not os.path.isfile(document_abs):
                print(
                    f"Error: document not found for chapter '{ch_id}': "
                    f"{document_abs}",
                    file=sys.stderr,
                )
                sys.exit(1)
            article_documents.add(document.removeprefix("resources/"))

    ui_entries = []
    for ui_name in sorted(seen_ui):
        ui_entries.append(f'    <file compressed="true">{ui_name}</file>')

    article_entries = [
        f'    <file compressed="true">{document}</file>'
        for document in sorted(article_documents)
    ]

    # 写出 gresource.xml
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/app">
    <file preprocess="xml-stripblanks">window.ui</file>
    <file>style.css</file>
{chr(10).join(article_entries) if article_entries else '    <!-- 暂无文章 -->'}
  </gresource>
  <gresource prefix="/app/chapters">
{chr(10).join(ui_entries) if ui_entries else '    <!-- 暂无章节 -->'}
  </gresource>
  <gresource prefix="/app/data">
    <file compressed="true">chapters.json</file>
  </gresource>
  <gresource prefix="/app/icons">
    <file>icons/tiger.svg</file>
  </gresource>
</gresources>
"""
    os.makedirs(os.path.dirname(output_xml), exist_ok=True)
    with open(output_xml, "w", encoding="utf-8") as f:
        f.write(xml)

    # stdout 供 meson 解析: target_id|blp_relative_path|ui_filename（按 .ui 去重）
    for ui_name, blp_file in sorted(seen_ui.items()):
        target_id = os.path.splitext(ui_name)[0]
        print(f"{target_id}|{blp_file}|{ui_name}")


if __name__ == "__main__":
    main()
