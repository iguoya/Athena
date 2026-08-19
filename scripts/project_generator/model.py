"""Load and validate the project model described by resources/athena.json."""

from __future__ import annotations

import json
import re
from pathlib import Path


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
    chapter_ui = require_object(defaults.get("chapter_ui"), "defaults.chapter_ui")
    code_ui = require_object(chapter_ui.get("code"), "defaults.chapter_ui.code")
    default_blueprint = project_path(
        root,
        code_ui.get("blueprint"),
        "defaults.chapter_ui.code.blueprint",
        prefix="resources/ui",
    )
    validate_icon(root, defaults.get("chapter_icon"), "defaults.chapter_icon")
    validate_icon(root, defaults.get("subchapter_icon"), "defaults.subchapter_icon")

    seen_categories: set[str] = set()
    seen_code_classes: dict[str, str] = {}
    seen_ui: dict[str, str] = {}
    documents: set[str] = set()
    source_files: set[str] = set()
    bindings: list[dict] = []
    chapters_by_id: dict[str, dict] = {}
    chapter_count = 0
    subchapter_count = 0

    # 手册：现有 article 章节和各 code 章节总纲文档的合集，本地静态渲染，
    # 不依赖任何单个章节存在；顺序即手册目录顺序。overview_document 必须
    # 落在这个列表里，否则"本章总纲"按钮无处可跳。
    handbook_documents = require_list(
        config.get("handbook_documents", []), "handbook_documents"
    )
    handbook_document_paths: set[str] = set()
    for doc_index, doc_value in enumerate(handbook_documents):
        doc_path = project_path(
            root,
            doc_value,
            f"handbook_documents[{doc_index}]",
            prefix="resources/articles",
        )
        handbook_document_paths.add(doc_path)
        documents.add(doc_path.removeprefix("resources/"))

    categories = require_list(config.get("categories"), "categories")
    if not categories:
        raise ProjectError("categories must not be empty")

    for category_index, category_value in enumerate(categories):
        category = require_object(category_value, f"categories[{category_index}]")
        category_name = require_text(
            category.get("name"), f"categories[{category_index}].name"
        )
        if not CATEGORY_PATTERN.fullmatch(category_name):
            raise ProjectError(f"invalid category name: {category_name!r}")
        if category_name in seen_categories:
            raise ProjectError(f"duplicate category name: {category_name}")
        seen_categories.add(category_name)
        require_text(category.get("title"), f"category {category_name}.title")
        require_text(category.get("description"), f"category {category_name}.description")
        validate_icon(root, category.get("icon"), f"category {category_name}.icon")

        seen_chapters: set[str] = set()
        chapters = require_list(
            category.get("chapters"), f"category {category_name}.chapters"
        )
        for chapter_index, chapter_value in enumerate(chapters):
            chapter = require_object(
                chapter_value, f"category {category_name}.chapters[{chapter_index}]"
            )
            chapter_name = require_text(chapter.get("name"), "chapter.name")
            chapter_id = f"{category_name}.{chapter_name}"
            if not IDENTIFIER_PATTERN.fullmatch(chapter_name):
                raise ProjectError(
                    f"invalid chapter/class name for {chapter_id}: {chapter_name!r}"
                )
            if chapter_name in seen_chapters:
                raise ProjectError(f"duplicate chapter name: {chapter_id}")
            seen_chapters.add(chapter_name)
            chapter_count += 1

            require_text(chapter.get("title"), f"chapter {chapter_id}.title")
            require_text(chapter.get("description"), f"chapter {chapter_id}.description")
            validate_icon(root, chapter.get("icon"), f"chapter {chapter_id}.icon")
            previous_chapter = seen_code_classes.get(chapter_name)
            if previous_chapter:
                raise ProjectError(
                    f"code chapters {previous_chapter} and {chapter_id} "
                    f"both generate global class {chapter_name}"
                )
            seen_code_classes[chapter_name] = chapter_id
            if "source" in chapter:
                source_files.add(project_path(
                    root,
                    chapter["source"],
                    f"chapter {chapter_id}.source",
                    prefix="language",
                ))

            custom_ui = chapter.get("ui")
            if custom_ui is None:
                blueprint = default_blueprint
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
                    f"blueprints {previous_blueprint!r} and {blueprint!r} "
                    f"both generate {ui_name!r}"
                )
            seen_ui[ui_name] = blueprint

            # 本章总纲：必须已经在 handbook_documents 里，"本章总纲"按钮
            # 跳的是手册里对应文档的锚点，指向一份手册没收录的文档没有
            # 意义。
            overview_document = chapter.get("overview_document")
            if overview_document is not None:
                overview_document = project_path(
                    root,
                    overview_document,
                    f"chapter {chapter_id}.overview_document",
                    prefix="resources/articles",
                )
                if overview_document not in handbook_document_paths:
                    raise ProjectError(
                        f"chapter {chapter_id}.overview_document "
                        f"{overview_document!r} is not listed in handbook_documents"
                    )

            groups = require_list(
                chapter.get("groups", []), f"chapter {chapter_id}.groups"
            )
            group_names: set[str] = set()
            for group_index, group_value in enumerate(groups):
                group = require_object(
                    group_value, f"chapter {chapter_id}.groups[{group_index}]"
                )
                group_name = require_text(
                    group.get("name"), f"chapter {chapter_id} group.name"
                )
                if not IDENTIFIER_PATTERN.fullmatch(group_name):
                    raise ProjectError(
                        f"invalid group name in {chapter_id}: {group_name!r}"
                    )
                if group_name in group_names:
                    raise ProjectError(
                        f"duplicate group name in {chapter_id}: {group_name}"
                    )
                group_names.add(group_name)
                require_text(
                    group.get("title"), f"chapter {chapter_id} group {group_name}.title"
                )
                require_text(
                    group.get("description"),
                    f"chapter {chapter_id} group {group_name}.description",
                )
                validate_icon(
                    root,
                    group.get("icon"),
                    f"chapter {chapter_id} group {group_name}.icon",
                )
                if "source" in group:
                    source_files.add(project_path(
                        root,
                        group["source"],
                        f"chapter {chapter_id} group {group_name}.source",
                        prefix="language",
                    ))

            subchapters = require_list(
                chapter.get("subchapters"), f"chapter {chapter_id}.subchapters"
            )
            seen_methods: set[str] = set()
            methods: list[str] = []
            for sub_index, sub_value in enumerate(subchapters):
                subchapter = require_object(
                    sub_value, f"chapter {chapter_id}.subchapters[{sub_index}]"
                )
                method = require_text(
                    subchapter.get("name"), f"chapter {chapter_id} subchapter.name"
                )
                if not IDENTIFIER_PATTERN.fullmatch(method):
                    raise ProjectError(
                        f"invalid method name in {chapter_id}: {method!r}"
                    )
                if method in seen_methods:
                    raise ProjectError(
                        f"duplicate subchapter name in {chapter_id}: {method}"
                    )
                seen_methods.add(method)
                methods.append(method)
                subchapter_count += 1
                require_text(
                    subchapter.get("title"),
                    f"chapter {chapter_id} subchapter {method}.title",
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
                if "importance" in subchapter:
                    importance = subchapter["importance"]
                    if not isinstance(importance, int) or isinstance(importance, bool) \
                            or not (0 <= importance <= 5):
                        raise ProjectError(
                            f"subchapter {chapter_id}.{method}.importance must be "
                            f"an integer in [0, 5], got {importance!r}"
                        )
                if "source" in subchapter:
                    source_files.add(project_path(
                        root,
                        subchapter["source"],
                        f"chapter {chapter_id} subchapter {method}.source",
                        prefix="language",
                    ))

            implementation = chapter.get("implementation")
            if implementation is not None:
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
                source_files.add(header)
                if "source" in implementation:
                    source_files.add(project_path(
                        root,
                        implementation["source"],
                        f"chapter {chapter_id}.implementation.source",
                        prefix="language",
                        must_exist=chapter_id != allow_missing_header_for,
                    ))
                if not methods:
                    raise ProjectError(
                        f"implemented chapter has no subchapters: {chapter_id}"
                    )
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
                    "methods": methods,
                }
            )
            chapters_by_id[chapter_id] = chapter_model

    return {
        "config": config,
        "ui": seen_ui,
        "documents": documents,
        "source_files": source_files,
        "bindings": bindings,
        "chapters": chapters_by_id,
        "category_count": len(categories),
        "chapter_count": chapter_count,
        "subchapter_count": subchapter_count,
    }
