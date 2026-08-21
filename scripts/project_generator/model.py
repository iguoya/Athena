"""Load, strictly validate, and normalize resources/athena.json."""

from __future__ import annotations

import json
import re
from pathlib import Path


CATEGORY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CXX20_KEYWORDS = frozenset(
    """
    alignas alignof and and_eq asm auto bitand bitor bool break case catch char
    char8_t char16_t char32_t class compl concept const consteval constexpr
    constinit const_cast continue co_await co_return co_yield decltype default
    delete do double dynamic_cast else enum explicit export extern false float
    for friend goto if inline int long mutable namespace new noexcept not not_eq
    nullptr operator or or_eq private protected public register reinterpret_cast
    requires return short signed sizeof static static_assert static_cast struct
    switch template this thread_local throw true try typedef typeid typename
    union unsigned using virtual void volatile wchar_t while xor xor_eq
    """.split()
)

ROOT_FIELDS = frozenset({"format_version", "defaults", "categories"})
DEFAULT_FIELDS = frozenset({"chapter_ui", "chapter_icon", "subchapter_icon"})
CHAPTER_UI_FIELDS = frozenset({"code"})
CODE_UI_FIELDS = frozenset({"blueprint"})
CATEGORY_FIELDS = frozenset(
    {"name", "title", "description", "icon", "handbook_documents", "chapters"}
)
CHAPTER_FIELDS = frozenset(
    {
        "name",
        "title",
        "description",
        "overview_document",
        "icon",
        "ui",
        "source",
        "implementation",
        "groups",
        "subchapters",
    }
)
IMPLEMENTATION_FIELDS = frozenset({"header", "source"})
UI_FIELDS = frozenset({"blueprint"})
GROUP_FIELDS = frozenset({"name", "title", "description", "icon", "source"})
SUBCHAPTER_FIELDS = frozenset(
    {"name", "title", "description", "importance", "icon", "group", "source"}
)


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


def reject_unknown_fields(
    value: dict,
    allowed: frozenset[str],
    label: str,
    *,
    deprecated: dict[str, str] | None = None,
) -> None:
    deprecated = deprecated or {}
    for field in sorted(value.keys() - allowed):
        if field in deprecated:
            raise ProjectError(f"{label}.{field} is deprecated; {deprecated[field]}")
        raise ProjectError(f"{label} contains unknown field {field!r}")


def validate_cpp_identifier(value: str, label: str, role: str) -> None:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ProjectError(f"{label} must be a valid C++ {role}: {value!r}")
    if value in CXX20_KEYWORDS:
        raise ProjectError(f"{label} must not be a C++20 keyword: {value!r}")


def project_path(
    root: Path,
    value: object,
    label: str,
    *,
    prefix: str | None = None,
    must_exist: bool = True,
) -> str:
    path = require_text(value, label)
    if "\\" in path:
        raise ProjectError(f"{label} must use '/' path separators: {path!r}")
    parts = Path(path).parts
    if Path(path).is_absolute() or "." in parts or ".." in parts:
        raise ProjectError(f"{label} must be a safe project-relative path: {path!r}")
    if prefix and not path.startswith(prefix.rstrip("/") + "/"):
        raise ProjectError(f"{label} must be stored under {prefix}/: {path}")
    if must_exist and not (root / path).is_file():
        raise ProjectError(f"{label} not found: {path}")
    return path


def blueprint_path(root: Path, value: object, label: str) -> str:
    path = project_path(root, value, label, prefix="resources/ui")
    if Path(path).suffix != ".blp":
        raise ProjectError(f"{label} must name a .blp file: {path!r}")
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
    return require_object(config, "athena.json")


def validate_icon(root: Path, value: object, label: str) -> dict:
    icon = require_object(value, label)
    icon_type = require_text(icon.get("type"), f"{label}.type")
    if icon_type == "theme":
        reject_unknown_fields(icon, frozenset({"type", "name"}), label)
        return {
            "type": "theme",
            "name": require_text(icon.get("name"), f"{label}.name"),
            "path": "",
        }
    if icon_type == "resource":
        reject_unknown_fields(icon, frozenset({"type", "path"}), label)
        return {
            "type": "resource",
            "name": "",
            "path": project_path(
                root,
                icon.get("path"),
                f"{label}.path",
                prefix="resources/icons",
            ),
        }
    raise ProjectError(f"{label}.type must be 'theme' or 'resource'")


def resolve_icon(icon: dict | None, fallback: dict | None, label: str) -> dict:
    resolved = icon or fallback
    if resolved is None:
        raise ProjectError(f"{label} must be provided or have a configured default")
    return dict(resolved)


def build_model(
    config_path: Path,
    root: Path,
    *,
    allow_missing_header_for: str | None = None,
) -> dict:
    config = load_json(config_path)
    reject_unknown_fields(
        config,
        ROOT_FIELDS,
        "athena.json",
        deprecated={
            "schema": "rename this old version field to format_version",
            "handbook_documents": (
                "move it into the owning category; handbooks are category-local"
            )
        },
    )
    format_version = config.get("format_version")
    if (
        not isinstance(format_version, int)
        or isinstance(format_version, bool)
        or format_version != 1
    ):
        raise ProjectError(
            f"unsupported athena.json format_version: {format_version!r}"
        )

    defaults = require_object(config.get("defaults"), "athena.json.defaults")
    reject_unknown_fields(
        defaults,
        DEFAULT_FIELDS,
        "athena.json.defaults",
        deprecated={"content": "content types were replaced by category handbooks"},
    )
    chapter_ui = require_object(
        defaults.get("chapter_ui"), "athena.json.defaults.chapter_ui"
    )
    reject_unknown_fields(
        chapter_ui,
        CHAPTER_UI_FIELDS,
        "athena.json.defaults.chapter_ui",
        deprecated={"article": "article chapters were replaced by category handbooks"},
    )
    code_ui = require_object(
        chapter_ui.get("code"), "athena.json.defaults.chapter_ui.code"
    )
    reject_unknown_fields(
        code_ui, CODE_UI_FIELDS, "athena.json.defaults.chapter_ui.code"
    )
    default_blueprint = blueprint_path(
        root,
        code_ui.get("blueprint"),
        "athena.json.defaults.chapter_ui.code.blueprint",
    )
    default_chapter_icon = (
        validate_icon(
            root,
            defaults["chapter_icon"],
            "athena.json.defaults.chapter_icon",
        )
        if "chapter_icon" in defaults
        else None
    )
    default_subchapter_icon = (
        validate_icon(
            root,
            defaults["subchapter_icon"],
            "athena.json.defaults.subchapter_icon",
        )
        if "subchapter_icon" in defaults
        else None
    )

    seen_categories: set[str] = set()
    seen_code_classes: dict[str, str] = {}
    seen_ui: dict[str, str] = {}
    documents: set[str] = set()
    source_files: set[str] = set()
    bindings: list[dict] = []
    chapters_by_id: dict[str, dict] = {}
    runtime_categories: list[dict] = []
    chapter_count = 0
    subchapter_count = 0

    categories = require_list(config.get("categories"), "athena.json.categories")
    if not categories:
        raise ProjectError("athena.json.categories must not be empty")

    for category_index, category_value in enumerate(categories):
        category_path = f"athena.json.categories[{category_index}]"
        category = require_object(category_value, category_path)
        reject_unknown_fields(
            category,
            CATEGORY_FIELDS,
            category_path,
            deprecated={"order": "array order is the display order"},
        )
        category_name = require_text(category.get("name"), f"{category_path}.name")
        if not CATEGORY_PATTERN.fullmatch(category_name):
            raise ProjectError(
                f"{category_path}.name must be lower ASCII snake_case: "
                f"{category_name!r}"
            )
        if category_name in seen_categories:
            raise ProjectError(f"duplicate category name: {category_name}")
        seen_categories.add(category_name)
        category_title = require_text(category.get("title"), f"{category_path}.title")
        category_description = require_text(
            category.get("description"), f"{category_path}.description"
        )
        category_icon = validate_icon(
            root, category.get("icon"), f"{category_path}.icon"
        )

        handbook_values = require_list(
            category.get("handbook_documents", []),
            f"{category_path}.handbook_documents",
        )
        handbook_documents: list[str] = []
        handbook_document_paths: set[str] = set()
        for doc_index, doc_value in enumerate(handbook_values):
            doc_path = project_path(
                root,
                doc_value,
                f"{category_path}.handbook_documents[{doc_index}]",
                prefix="resources/articles",
            )
            if doc_path in handbook_document_paths:
                raise ProjectError(
                    f"duplicate handbook document in category {category_name}: "
                    f"{doc_path}"
                )
            handbook_document_paths.add(doc_path)
            handbook_documents.append(doc_path)
            documents.add(doc_path.removeprefix("resources/"))

        runtime_chapters: list[dict] = []
        seen_chapters: set[str] = set()
        chapters = require_list(category.get("chapters"), f"{category_path}.chapters")
        for chapter_index, chapter_value in enumerate(chapters):
            chapter_path = f"{category_path}.chapters[{chapter_index}]"
            chapter = require_object(chapter_value, chapter_path)
            reject_unknown_fields(
                chapter,
                CHAPTER_FIELDS,
                chapter_path,
                deprecated={
                    "content": "article chapters were replaced by category handbooks",
                    "document": "put the document in category.handbook_documents",
                    "order": "array order is the display order",
                },
            )
            chapter_name = require_text(chapter.get("name"), f"{chapter_path}.name")
            chapter_id = f"{category_name}.{chapter_name}"
            validate_cpp_identifier(chapter_name, f"{chapter_path}.name", "class name")
            if chapter_name in seen_chapters:
                raise ProjectError(f"duplicate chapter name: {chapter_id}")
            seen_chapters.add(chapter_name)
            chapter_count += 1

            chapter_title = require_text(chapter.get("title"), f"{chapter_path}.title")
            chapter_description = require_text(
                chapter.get("description"), f"{chapter_path}.description"
            )
            own_chapter_icon = (
                validate_icon(root, chapter["icon"], f"{chapter_path}.icon")
                if "icon" in chapter
                else None
            )
            chapter_icon = resolve_icon(
                own_chapter_icon, default_chapter_icon, f"{chapter_path}.icon"
            )
            previous_chapter = seen_code_classes.get(chapter_name)
            if previous_chapter:
                raise ProjectError(
                    f"code chapters {previous_chapter} and {chapter_id} "
                    f"both generate global class {chapter_name}"
                )
            seen_code_classes[chapter_name] = chapter_id

            implementation = chapter.get("implementation")
            implementation_header = ""
            if "implementation" in chapter:
                implementation = require_object(
                    implementation, f"{chapter_path}.implementation"
                )
                reject_unknown_fields(
                    implementation,
                    IMPLEMENTATION_FIELDS,
                    f"{chapter_path}.implementation",
                )
                implementation_header = project_path(
                    root,
                    implementation.get("header"),
                    f"{chapter_path}.implementation.header",
                    prefix="language",
                    must_exist=chapter_id != allow_missing_header_for,
                )
                source_files.add(implementation_header)
                if "source" in implementation:
                    source_files.add(
                        project_path(
                            root,
                            implementation["source"],
                            f"{chapter_path}.implementation.source",
                            prefix="language",
                            must_exist=chapter_id != allow_missing_header_for,
                        )
                    )

            chapter_source = implementation_header
            if "source" in chapter:
                chapter_source = project_path(
                    root,
                    chapter["source"],
                    f"{chapter_path}.source",
                    prefix="language",
                )
                source_files.add(chapter_source)

            custom_ui = chapter.get("ui")
            if "ui" not in chapter:
                blueprint = default_blueprint
            else:
                custom_ui = require_object(custom_ui, f"{chapter_path}.ui")
                reject_unknown_fields(custom_ui, UI_FIELDS, f"{chapter_path}.ui")
                blueprint = blueprint_path(
                    root,
                    custom_ui.get("blueprint"),
                    f"{chapter_path}.ui.blueprint",
                )
            ui_name = Path(blueprint).with_suffix(".ui").name
            previous_blueprint = seen_ui.get(ui_name)
            if previous_blueprint and previous_blueprint != blueprint:
                raise ProjectError(
                    f"blueprints {previous_blueprint!r} and {blueprint!r} "
                    f"both generate {ui_name!r}"
                )
            seen_ui[ui_name] = blueprint
            stem = Path(blueprint).stem

            overview_document = ""
            if "overview_document" in chapter:
                overview_document = project_path(
                    root,
                    chapter["overview_document"],
                    f"{chapter_path}.overview_document",
                    prefix="resources/articles",
                )
                if overview_document not in handbook_document_paths:
                    raise ProjectError(
                        f"{chapter_path}.overview_document {overview_document!r} "
                        f"is not listed in category {category_name}.handbook_documents"
                    )

            runtime_groups: list[dict] = []
            group_names: set[str] = set()
            group_sources: dict[str, str] = {}
            groups = require_list(chapter.get("groups", []), f"{chapter_path}.groups")
            for group_index, group_value in enumerate(groups):
                group_path = f"{chapter_path}.groups[{group_index}]"
                group = require_object(group_value, group_path)
                reject_unknown_fields(
                    group,
                    GROUP_FIELDS,
                    group_path,
                    deprecated={"order": "array order is the display order"},
                )
                group_name = require_text(group.get("name"), f"{group_path}.name")
                if not IDENTIFIER_PATTERN.fullmatch(group_name):
                    raise ProjectError(
                        f"{group_path}.name must be an ASCII identifier: "
                        f"{group_name!r}"
                    )
                if group_name in group_names:
                    raise ProjectError(
                        f"duplicate group name in {chapter_id}: {group_name}"
                    )
                group_names.add(group_name)
                group_title = require_text(group.get("title"), f"{group_path}.title")
                group_description = require_text(
                    group.get("description"), f"{group_path}.description"
                )
                own_group_icon = (
                    validate_icon(root, group["icon"], f"{group_path}.icon")
                    if "icon" in group
                    else None
                )
                group_source = ""
                if "source" in group:
                    group_source = project_path(
                        root,
                        group["source"],
                        f"{group_path}.source",
                        prefix="language",
                    )
                    source_files.add(group_source)
                group_sources[group_name] = group_source
                runtime_groups.append(
                    {
                        "name": group_name,
                        "title": group_title,
                        "description": group_description,
                        "source": group_source,
                        "icon": resolve_icon(
                            own_group_icon, chapter_icon, f"{group_path}.icon"
                        ),
                    }
                )

            runtime_subchapters: list[dict] = []
            seen_methods: set[str] = set()
            methods: list[str] = []
            function_ids: list[str] = []
            subchapters = require_list(
                chapter.get("subchapters"), f"{chapter_path}.subchapters"
            )
            for sub_index, sub_value in enumerate(subchapters):
                subchapter_path = f"{chapter_path}.subchapters[{sub_index}]"
                subchapter = require_object(sub_value, subchapter_path)
                reject_unknown_fields(
                    subchapter,
                    SUBCHAPTER_FIELDS,
                    subchapter_path,
                    deprecated={
                        "id": "use name as the stable local identifier",
                        "method": "use name as the C++ member function name",
                        "order": "array order is the display order",
                    },
                )
                method = require_text(
                    subchapter.get("name"), f"{subchapter_path}.name"
                )
                validate_cpp_identifier(
                    method, f"{subchapter_path}.name", "member function name"
                )
                if method in seen_methods:
                    raise ProjectError(
                        f"duplicate subchapter name in {chapter_id}: {method}"
                    )
                seen_methods.add(method)
                methods.append(method)
                function_id = f"{chapter_id}.{method}"
                function_ids.append(function_id)
                subchapter_count += 1
                subchapter_title = require_text(
                    subchapter.get("title"), f"{subchapter_path}.title"
                )
                subchapter_description = require_text(
                    subchapter.get("description"), f"{subchapter_path}.description"
                )
                own_subchapter_icon = (
                    validate_icon(
                        root, subchapter["icon"], f"{subchapter_path}.icon"
                    )
                    if "icon" in subchapter
                    else None
                )
                group_name = ""
                if "group" in subchapter:
                    group_name = require_text(
                        subchapter["group"], f"{subchapter_path}.group"
                    )
                    if group_name not in group_names:
                        raise ProjectError(
                            f"{subchapter_path}.group references unknown group "
                            f"{group_name!r}"
                        )
                importance = subchapter.get("importance", 0)
                if (
                    not isinstance(importance, int)
                    or isinstance(importance, bool)
                    or not 0 <= importance <= 5
                ):
                    raise ProjectError(
                        f"{subchapter_path}.importance must be an integer in [0, 5], "
                        f"got {importance!r}"
                    )
                resolved_source = group_sources.get(group_name, "") or chapter_source
                if "source" in subchapter:
                    resolved_source = project_path(
                        root,
                        subchapter["source"],
                        f"{subchapter_path}.source",
                        prefix="language",
                    )
                    source_files.add(resolved_source)
                runtime_subchapters.append(
                    {
                        "function_id": function_id,
                        "name": method,
                        "title": subchapter_title,
                        "description": subchapter_description,
                        "group": group_name,
                        "source": resolved_source,
                        "importance": importance,
                        "icon": resolve_icon(
                            own_subchapter_icon,
                            default_subchapter_icon,
                            f"{subchapter_path}.icon",
                        ),
                    }
                )

            if implementation is not None:
                if not methods:
                    raise ProjectError(
                        f"implemented chapter has no subchapters: {chapter_id}"
                    )
                bindings.append(
                    {
                        "category": category_name,
                        "chapter": chapter_name,
                        "header": implementation_header,
                        "methods": methods,
                        "function_ids": function_ids,
                    }
                )

            runtime_chapters.append(
                {
                    "name": chapter_name,
                    "title": chapter_title,
                    "description": chapter_description,
                    "overview_document": overview_document,
                    "resource_path": f"/app/chapters/{stem}.ui",
                    "widget_name": (
                        "chapter_page"
                        if blueprint == default_blueprint
                        else f"{stem}_page"
                    ),
                    "source": chapter_source,
                    "implementation_header": implementation_header,
                    "icon": chapter_icon,
                    "groups": runtime_groups,
                    "subchapters": runtime_subchapters,
                }
            )

            chapter_model = dict(chapter)
            chapter_model.update(
                {
                    "id": chapter_id,
                    "category": category_name,
                    "methods": methods,
                    "function_ids": function_ids,
                }
            )
            chapters_by_id[chapter_id] = chapter_model

        runtime_categories.append(
            {
                "name": category_name,
                "title": category_title,
                "description": category_description,
                "icon": category_icon,
                "handbook_documents": handbook_documents,
                "chapters": runtime_chapters,
            }
        )

    return {
        "config": config,
        "runtime_catalog": {
            "catalog_version": 1,
            "categories": runtime_categories,
        },
        "ui": seen_ui,
        "documents": documents,
        "source_files": source_files,
        "bindings": bindings,
        "chapters": chapters_by_id,
        "category_count": len(categories),
        "chapter_count": chapter_count,
        "subchapter_count": subchapter_count,
    }
