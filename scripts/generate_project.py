#!/usr/bin/env python3
"""Validate Athena's project model and generate build/scaffold artifacts.

``resources/athena.json`` is the single source of truth.  This command only
derives files from that model; generated build artifacts should not be edited.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


CONTENT_TYPES = {"article", "code"}
CATEGORY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ProjectError(ValueError):
    """A user-facing project configuration error."""


def require_object(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise ProjectError(f"{label} must be an object")
    return value


def require_list(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise ProjectError(f"{label} must be an array")
    return value


def require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectError(f"{label} must be a non-empty string")
    return value


def project_path(
    root: Path,
    value: object,
    label: str,
    *,
    prefix: str | None = None,
    must_exist: bool = True,
) -> str:
    path = require_text(value, label).replace("\\", "/")
    parts = Path(path).parts
    if Path(path).is_absolute() or "." in parts or ".." in parts:
        raise ProjectError(f"{label} must be a safe project-relative path: {path!r}")
    if prefix and not path.startswith(prefix.rstrip("/") + "/"):
        raise ProjectError(f"{label} must be stored under {prefix}/: {path}")
    if must_exist and not (root / path).is_file():
        raise ProjectError(f"{label} not found: {path}")
    return path


def load_json(config_path: Path) -> dict:
    try:
        with config_path.open(encoding="utf-8") as source:
            config = json.load(source)
    except OSError as error:
        raise ProjectError(f"cannot read config {config_path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ProjectError(
            f"invalid JSON in {config_path}:{error.lineno}:{error.colno}: {error.msg}"
        ) from error
    return require_object(config, "project config")


def validate_icon(root: Path, icon: object, label: str) -> None:
    if icon is None:
        return
    icon = require_object(icon, label)
    icon_type = require_text(icon.get("type"), f"{label}.type")
    if icon_type == "theme":
        require_text(icon.get("name"), f"{label}.name")
    elif icon_type == "resource":
        project_path(
            root,
            icon.get("path"),
            f"{label}.path",
            prefix="resources/icons",
        )
    else:
        raise ProjectError(f"{label}.type must be 'theme' or 'resource'")


def build_model(
    config_path: Path,
    root: Path,
    *,
    allow_missing_header_for: str | None = None,
) -> dict:
    config = load_json(config_path)
    if config.get("schema") != 1:
        raise ProjectError(f"unsupported athena.json schema: {config.get('schema')!r}")

    defaults = require_object(config.get("defaults"), "defaults")
    default_content = defaults.get("content", "code")
    if default_content not in CONTENT_TYPES:
        raise ProjectError(f"unsupported defaults.content: {default_content!r}")
    chapter_ui = require_object(defaults.get("chapter_ui"), "defaults.chapter_ui")
    default_blueprints = {}
    for content in sorted(CONTENT_TYPES):
        ui = require_object(chapter_ui.get(content), f"defaults.chapter_ui.{content}")
        default_blueprints[content] = project_path(
            root,
            ui.get("blueprint"),
            f"defaults.chapter_ui.{content}.blueprint",
            prefix="resources/ui",
        )
    validate_icon(root, defaults.get("chapter_icon"), "defaults.chapter_icon")
    validate_icon(root, defaults.get("subchapter_icon"), "defaults.subchapter_icon")

    categories = require_list(config.get("categories"), "categories")
    if not categories:
        raise ProjectError("categories must not be empty")

    seen_categories: set[str] = set()
    seen_ui: dict[str, str] = {}
    documents: set[str] = set()
    bindings: list[dict] = []
    chapters_by_id: dict[str, dict] = {}
    chapter_count = 0
    subchapter_count = 0

    for category_index, category_value in enumerate(categories):
        category = require_object(category_value, f"categories[{category_index}]")
        category_name = require_text(category.get("name"), f"categories[{category_index}].name")
        if not CATEGORY_PATTERN.fullmatch(category_name):
            raise ProjectError(f"invalid category name: {category_name!r}")
        if category_name in seen_categories:
            raise ProjectError(f"duplicate category name: {category_name}")
        seen_categories.add(category_name)
        require_text(category.get("title"), f"category {category_name}.title")
        require_text(category.get("description"), f"category {category_name}.description")
        validate_icon(root, category.get("icon"), f"category {category_name}.icon")

        seen_chapters: set[str] = set()
        for chapter_index, chapter_value in enumerate(
            require_list(category.get("chapters"), f"category {category_name}.chapters")
        ):
            chapter = require_object(
                chapter_value, f"category {category_name}.chapters[{chapter_index}]"
            )
            chapter_name = require_text(chapter.get("name"), "chapter.name")
            chapter_id = f"{category_name}.{chapter_name}"
            if not IDENTIFIER_PATTERN.fullmatch(chapter_name):
                raise ProjectError(f"invalid chapter/class name for {chapter_id}: {chapter_name!r}")
            if chapter_name in seen_chapters:
                raise ProjectError(f"duplicate chapter name: {chapter_id}")
            seen_chapters.add(chapter_name)
            chapter_count += 1

            require_text(chapter.get("title"), f"chapter {chapter_id}.title")
            require_text(chapter.get("description"), f"chapter {chapter_id}.description")
            validate_icon(root, chapter.get("icon"), f"chapter {chapter_id}.icon")
            content = chapter.get("content", default_content)
            if content not in CONTENT_TYPES:
                raise ProjectError(f"chapter {chapter_id} has unsupported content {content!r}")
            if "source" in chapter:
                project_path(
                    root,
                    chapter["source"],
                    f"chapter {chapter_id}.source",
                    prefix="language",
                )

            custom_ui = chapter.get("ui")
            if custom_ui is None:
                blueprint = default_blueprints[content]
            else:
                custom_ui = require_object(custom_ui, f"chapter {chapter_id}.ui")
                blueprint = project_path(
                    root,
                    custom_ui.get("blueprint"),
                    f"chapter {chapter_id}.ui.blueprint",
                    prefix="resources/ui",
                )
            ui_name = Path(blueprint).with_suffix(".ui").name
            previous_blueprint = seen_ui.get(ui_name)
            if previous_blueprint and previous_blueprint != blueprint:
                raise ProjectError(
                    f"blueprints {previous_blueprint!r} and {blueprint!r} both generate {ui_name!r}"
                )
            seen_ui[ui_name] = blueprint

            document = chapter.get("document")
            if document is not None:
                document = project_path(
                    root,
                    document,
                    f"chapter {chapter_id}.document",
                    prefix="resources/articles",
                )
                documents.add(document.removeprefix("resources/"))
            if content == "article" and custom_ui is None and document is None:
                raise ProjectError(f"article chapter {chapter_id} requires a document")

            groups = require_list(chapter.get("groups", []), f"chapter {chapter_id}.groups")
            group_names: set[str] = set()
            for group_index, group_value in enumerate(groups):
                group = require_object(group_value, f"chapter {chapter_id}.groups[{group_index}]")
                group_name = require_text(group.get("name"), f"chapter {chapter_id} group.name")
                if not IDENTIFIER_PATTERN.fullmatch(group_name):
                    raise ProjectError(f"invalid group name in {chapter_id}: {group_name!r}")
                if group_name in group_names:
                    raise ProjectError(f"duplicate group name in {chapter_id}: {group_name}")
                group_names.add(group_name)
                require_text(group.get("title"), f"chapter {chapter_id} group {group_name}.title")
                require_text(
                    group.get("description"),
                    f"chapter {chapter_id} group {group_name}.description",
                )
                validate_icon(root, group.get("icon"), f"chapter {chapter_id} group {group_name}.icon")
                if "source" in group:
                    project_path(
                        root,
                        group["source"],
                        f"chapter {chapter_id} group {group_name}.source",
                        prefix="language",
                    )

            subchapters = require_list(
                chapter.get("subchapters"), f"chapter {chapter_id}.subchapters"
            )
            if content == "article" and (groups or subchapters):
                raise ProjectError(
                    f"article chapter {chapter_id} cannot declare groups or subchapters"
                )
            seen_methods: set[str] = set()
            methods: list[str] = []
            for sub_index, sub_value in enumerate(subchapters):
                subchapter = require_object(
                    sub_value, f"chapter {chapter_id}.subchapters[{sub_index}]"
                )
                method = require_text(subchapter.get("name"), f"chapter {chapter_id} subchapter.name")
                if not IDENTIFIER_PATTERN.fullmatch(method):
                    raise ProjectError(f"invalid method name in {chapter_id}: {method!r}")
                if method in seen_methods:
                    raise ProjectError(f"duplicate subchapter name in {chapter_id}: {method}")
                seen_methods.add(method)
                methods.append(method)
                subchapter_count += 1
                require_text(
                    subchapter.get("title"), f"chapter {chapter_id} subchapter {method}.title"
                )
                require_text(
                    subchapter.get("description"),
                    f"chapter {chapter_id} subchapter {method}.description",
                )
                validate_icon(
                    root,
                    subchapter.get("icon"),
                    f"chapter {chapter_id} subchapter {method}.icon",
                )
                group = subchapter.get("group")
                if group is not None and group not in group_names:
                    raise ProjectError(
                        f"subchapter {chapter_id}.{method} references unknown group {group!r}"
                    )
                if "source" in subchapter:
                    project_path(
                        root,
                        subchapter["source"],
                        f"chapter {chapter_id} subchapter {method}.source",
                        prefix="language",
                    )

            implementation = chapter.get("implementation")
            if implementation is not None:
                if content != "code":
                    raise ProjectError(f"only code chapters can declare implementation: {chapter_id}")
                implementation = require_object(
                    implementation, f"chapter {chapter_id}.implementation"
                )
                header = project_path(
                    root,
                    implementation.get("header"),
                    f"chapter {chapter_id}.implementation.header",
                    prefix="language",
                    must_exist=chapter_id != allow_missing_header_for,
                )
                if "source" in implementation:
                    project_path(
                        root,
                        implementation["source"],
                        f"chapter {chapter_id}.implementation.source",
                        prefix="language",
                        must_exist=chapter_id != allow_missing_header_for,
                    )
                if not methods:
                    raise ProjectError(f"implemented chapter has no subchapters: {chapter_id}")
                bindings.append(
                    {
                        "category": category_name,
                        "chapter": chapter_name,
                        "header": header,
                        "methods": methods,
                    }
                )

            chapter_model = dict(chapter)
            chapter_model.update(
                {
                    "id": chapter_id,
                    "category": category_name,
                    "content": content,
                    "methods": methods,
                }
            )
            chapters_by_id[chapter_id] = chapter_model

    return {
        "config": config,
        "ui": seen_ui,
        "documents": documents,
        "bindings": bindings,
        "chapters": chapters_by_id,
        "category_count": len(categories),
        "chapter_count": chapter_count,
        "subchapter_count": subchapter_count,
    }


def write_generated(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_name = temporary.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def write_new(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
    except FileExistsError:
        return False
    return True


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


def render_registry(bindings: list[dict]) -> str:
    headers = sorted({binding["header"] for binding in bindings})
    lines = [
        "// Generated from resources/athena.json by generate_project.py. DO NOT EDIT.",
        '#include "registry/function_registry.h"',
        "",
    ]
    lines.extend(f'#include "{header}"' for header in headers)
    lines.extend(["", "#include <memory>", "", "using namespace std;", ""])
    lines.extend(["FunctionRegistry create_default_function_registry() {", "    FunctionRegistry registry;"])
    for binding in bindings:
        category = binding["category"]
        chapter = binding["chapter"]
        variable = f"{category}_{chapter}".lower()
        class_name = f"athena::{category}::{chapter}"
        lines.append(f"    auto {variable} = make_shared<{class_name}>();")
        for method in binding["methods"]:
            lines.append(
                f'    registry.add(make_function_id("{category}", "{chapter}", "{method}"), '
                f"[{variable}](ostream& output) {{"
            )
            lines.append(f"        {variable}->{method}(output);")
            lines.append("    });")
        lines.append("")
    lines.extend(["    return registry;", "}", ""])
    return "\n".join(lines)


def cpp_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def scaffold(model: dict, root: Path, chapter_id: str) -> None:
    chapter = model["chapters"].get(chapter_id)
    if chapter is None:
        raise ProjectError(f"unknown chapter: {chapter_id}")
    if chapter["content"] != "code":
        raise ProjectError(f"cannot scaffold article chapter: {chapter_id}")
    implementation = chapter.get("implementation")
    if not isinstance(implementation, dict) or not implementation.get("header"):
        raise ProjectError(
            f"chapter {chapter_id} must declare implementation.header in athena.json first"
        )
    if not chapter["methods"]:
        raise ProjectError(f"chapter {chapter_id} has no subchapters to scaffold")

    header_rel = implementation["header"].replace("\\", "/")
    source_rel = implementation.get("source")
    if source_rel is None:
        source_rel = str(Path(header_rel).with_suffix(".cpp")).replace("\\", "/")
    source_rel = project_path(
        root,
        source_rel,
        f"chapter {chapter_id}.implementation.source",
        prefix="language",
        must_exist=False,
    )
    header_path = root / header_rel
    source_path = root / source_rel
    category = chapter["category"]
    class_name = chapter["name"]

    header_lines = [
        "#pragma once",
        "",
        "#include <iosfwd>",
        "",
        "using namespace std;",
        "",
        f"namespace athena::{category} {{",
        "",
        f"class {class_name} {{",
        "public:",
    ]
    header_lines.extend(f"    void {method}(ostream& output);" for method in chapter["methods"])
    header_lines.extend(["};", "", f"}}  // namespace athena::{category}", ""])

    source_lines = [
        f'#include "{Path(header_rel).name}"',
        "",
        "#include <ostream>",
        "",
        f"namespace athena::{category} {{",
        "",
    ]
    subchapters = {item["name"]: item for item in chapter["subchapters"]}
    for method in chapter["methods"]:
        title = subchapters[method]["title"]
        source_lines.extend(
            [
                f"void {class_name}::{method}(ostream& output) {{",
                f"    output << {cpp_string('[待实现] ' + title)} << '\\n';",
                "}",
                "",
            ]
        )
    source_lines.extend([f"}}  // namespace athena::{category}", ""])

    for path, content in (
        (header_path, "\n".join(header_lines)),
        (source_path, "\n".join(source_lines)),
    ):
        if write_new(path, content):
            print(f"created: {path.relative_to(root)}")
        else:
            print(f"kept: {path.relative_to(root)}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Athena and generate resources, registry, or chapter skeletons."
    )
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)

    resources = commands.add_parser("resources", help="generate GResource XML")
    resources.add_argument("--output", type=Path, required=True)
    registry = commands.add_parser("registry", help="generate FunctionRegistry C++")
    registry.add_argument("--output", type=Path, required=True)
    commands.add_parser("check", help="validate the project without writing files")
    scaffold_parser = commands.add_parser("scaffold", help="create a code chapter skeleton")
    scaffold_parser.add_argument("--chapter", required=True, metavar="CATEGORY.CHAPTER")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    root = args.project_root.resolve()
    config_path = args.config
    if not config_path.is_absolute():
        config_path = (Path.cwd() / config_path).resolve()
    allow_missing = args.chapter if args.command == "scaffold" else None
    model = build_model(config_path, root, allow_missing_header_for=allow_missing)

    if args.command == "resources":
        write_generated(args.output, render_resources(model, root))
        for ui_name, blueprint in sorted(model["ui"].items()):
            print(f"{Path(ui_name).stem}|{blueprint}|{ui_name}")
    elif args.command == "registry":
        write_generated(args.output, render_registry(model["bindings"]))
    elif args.command == "check":
        print(
            "athena.json is valid: "
            f"{model['category_count']} categories, "
            f"{model['chapter_count']} chapters, "
            f"{model['subchapter_count']} subchapters, "
            f"{len(model['bindings'])} implementations"
        )
    elif args.command == "scaffold":
        scaffold(model, root, args.chapter)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProjectError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
