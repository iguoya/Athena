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
        "prerequisites",
        "groups",
        "subchapters",
        "learning_units",
    }
)
IMPLEMENTATION_FIELDS = frozenset({"header", "source"})
UI_FIELDS = frozenset({"blueprint"})
GROUP_FIELDS = frozenset({"name", "title", "description", "icon", "source"})
SUBCHAPTER_FIELDS = frozenset(
    {
        "name",
        "title",
        "description",
        "difficulty",
        "mastery_goal",
        "knowledge_type",
        "requires",
        "icon",
        "group",
        "source",
        "teaches",
    }
)
TEACHES_FIELDS = frozenset({"document", "heading"})
# 掌握目标：master 需要精通、required 必须掌握、familiar 一般了解；
# 空串表示尚未评定。评定依据是"日常使用频率 × 用错的代价"——天天要用且写错代价高的
# 才是需要精通，少见或只在特定场景出现的一般了解（ADR 0029）。
MASTERY_GOALS = frozenset({"", "master", "required", "familiar"})
# 知识类型决定该用哪种教学动作（ADR 0031）：concept 概念要正反例辨析，
# skill 程序性技能要示范加变式练习，strategy 条件性知识要情境判断加说明理由。
KNOWLEDGE_TYPES = frozenset({"", "concept", "skill", "strategy"})
LEARNING_UNIT_FIELDS = frozenset(
    {"id", "heading", "claim", "question", "choices", "correct_choice", "feedback", "follow_up", "experiment"}
)
ATX_HEADING_PATTERN = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*$")
TRAILING_HEADING_MARKS_PATTERN = re.compile(r"[ \t]+#+[ \t]*$")

# 教学/实践源码允许存放的两个顶层目录，互相平级：language/ 按 C++ 语言
# 特性拆分知识点，practice/ 收纳自成一体的应用实践项目（比如
# practice/pocket_cube/），不嵌在 language/ 下面。
SOURCE_PREFIXES = ("language", "practice")


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
    prefix: str | tuple[str, ...] | None = None,
    must_exist: bool = True,
) -> str:
    path = require_text(value, label)
    if "\\" in path:
        raise ProjectError(f"{label} must use '/' path separators: {path!r}")
    parts = Path(path).parts
    if Path(path).is_absolute() or "." in parts or ".." in parts:
        raise ProjectError(f"{label} must be a safe project-relative path: {path!r}")
    if prefix:
        # 允许指定一组候选前缀，只要落在其中一个下面就行——source_files
        # 既有 language/ 下按语言特性拆分的教学代码，也有 practice/ 下
        # 自成一体的应用实践项目代码，两者是同级目录，不是前者的子集。
        prefixes = (prefix,) if isinstance(prefix, str) else prefix
        if not any(path.startswith(p.rstrip("/") + "/") for p in prefixes):
            allowed = " or ".join(f"{p}/" for p in prefixes)
            raise ProjectError(f"{label} must be stored under {allowed}: {path}")
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


def markdown_heading_titles(path: Path) -> list[str]:
    """Return normalized ATX heading text, ignoring fenced code examples."""
    titles: list[str] = []
    fence: str | None = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ProjectError(f"cannot read handbook document {path}: {error}") from error

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            continue

        match = ATX_HEADING_PATTERN.match(line)
        if not match:
            continue
        title = TRAILING_HEADING_MARKS_PATTERN.sub("", match.group(2)).strip()
        # teaches.heading deliberately targets short, plain titles. Removing the
        # common inline emphasis markers keeps validation aligned with MD4C's
        # visible heading text while avoiding a second Markdown parser in Python.
        title = re.sub(r"[`*_~]", "", title)
        titles.append(" ".join(title.split()))
    return titles


def validate_prerequisite_graph(
    prerequisites_by_name: dict[str, list[str]], category_name: str
) -> None:
    """Every prerequisite must name a chapter in the same category, and the
    resulting dependency graph must be acyclic (the knowledge-graph page lays
    it out in prerequisite layers)."""
    known = set(prerequisites_by_name)
    for chapter_name, prerequisites in prerequisites_by_name.items():
        for pre_name in prerequisites:
            if pre_name not in known:
                raise ProjectError(
                    f"chapter {category_name}.{chapter_name} lists unknown "
                    f"prerequisite {pre_name!r}; prerequisites must name a "
                    f"chapter in the same category"
                )

    # 三色 DFS 找环，报错时给出成环路径便于定位。
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in prerequisites_by_name}

    def visit(name: str, stack: list[str]) -> None:
        color[name] = GRAY
        stack.append(name)
        for pre_name in prerequisites_by_name[name]:
            if color[pre_name] == GRAY:
                cycle = stack[stack.index(pre_name):] + [pre_name]
                raise ProjectError(
                    f"prerequisite cycle in category {category_name}: "
                    + " -> ".join(cycle)
                )
            if color[pre_name] == WHITE:
                visit(pre_name, stack)
        stack.pop()
        color[name] = BLACK

    for name in prerequisites_by_name:
        if color[name] == WHITE:
            visit(name, [])


def validate_subchapter_requirements(
    requirements: dict[str, list[str]],
    locations: dict[str, str],
    chapter_of: dict[str, str],
    reachable_chapters: dict[str, set[str]],
) -> None:
    """知识点级前置依赖的全局校验（ADR 0030）。

    依赖用完整函数 ID 表示，必须指向真实存在的知识点、不能自引用、整体不能成环。
    跨章依赖还必须与章节 prerequisites 同向：只能依赖本章，或本章（传递）前置章节里
    的知识点——否则内容顺序自相矛盾，学习者永远不可能先学到它。
    """
    for function_id, required_ids in requirements.items():
        where = locations[function_id]
        for required_id in required_ids:
            if required_id == function_id:
                raise ProjectError(f"{where}.requires lists the knowledge point itself")
            if required_id not in requirements:
                raise ProjectError(
                    f"{where}.requires references unknown knowledge point "
                    f"{required_id!r}"
                )
            own_chapter = chapter_of[function_id]
            target_chapter = chapter_of[required_id]
            if target_chapter != own_chapter and target_chapter not in (
                reachable_chapters.get(own_chapter, set())
            ):
                raise ProjectError(
                    f"{where}.requires depends on {required_id!r} in chapter "
                    f"{target_chapter!r}, which is not this chapter nor one of its "
                    f"prerequisite chapters; knowledge-point dependencies must run "
                    f"the same direction as chapter prerequisites"
                )

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {function_id: WHITE for function_id in requirements}

    def visit(function_id: str, stack: list[str]) -> None:
        color[function_id] = GRAY
        stack.append(function_id)
        for required_id in requirements[function_id]:
            if color[required_id] == GRAY:
                cycle = stack[stack.index(required_id):] + [required_id]
                raise ProjectError(
                    "knowledge-point requirement cycle: " + " -> ".join(cycle)
                )
            if color[required_id] == WHITE:
                visit(required_id, stack)
        stack.pop()
        color[function_id] = BLACK

    for function_id in requirements:
        if color[function_id] == WHITE:
            visit(function_id, [])


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
    headings_by_document: dict[str, list[str]] = {}
    runtime_categories: list[dict] = []
    # 知识点级前置依赖跨章节、跨分类，收齐全部知识点后统一校验并展开成完整 ID。
    requirements_by_id: dict[str, list[str]] = {}
    requirement_locations: dict[str, str] = {}
    chapter_of_function: dict[str, str] = {}
    titles_by_function: dict[str, tuple[str, str]] = {}
    raw_requirements: list[tuple[str, str, str, list[str], dict]] = []
    prerequisites_by_chapter_id: dict[str, list[str]] = {}
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

            # 手册插图放在文档同级的 images/ 目录，随手册一起打包进
            # GResource：渲染层按 ![](images/xxx.svg) 引用，加载后内联成
            # data: URI，打包后无源码目录也能显示。
            images_dir = (root / doc_path).parent / "images"
            if images_dir.is_dir():
                for image in sorted(images_dir.glob("*.svg")):
                    documents.add(
                        image.relative_to(root)
                        .as_posix()
                        .removeprefix("resources/")
                    )

            # 每份手册文档正文末尾必须有一节「小结」/「本章小结」，
            # 概括要点、易错点和知识点关系（见 AGENTS.md）。
            doc_headings = headings_by_document.get(doc_path)
            if doc_headings is None:
                doc_headings = markdown_heading_titles(root / doc_path)
                headings_by_document[doc_path] = doc_headings
            if not any(title.endswith("小结") for title in doc_headings):
                raise ProjectError(
                    f"{category_path}.handbook_documents[{doc_index}] "
                    f"{doc_path!r} 缺少「小结」小节：手册文档正文末尾"
                    f"必须有一节标题为「小结」或「本章小结」的回顾"
                )

        runtime_chapters: list[dict] = []
        seen_chapters: set[str] = set()
        # chapter name -> 它声明的前置章节 name 列表（知识图谱的边）。同分类内
        # 引用，声明顺序无关；引用合法性和无环由本分类章节全部读完后统一校验。
        prerequisites_by_name: dict[str, list[str]] = {}
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

            prerequisite_names: list[str] = []
            seen_prerequisites: set[str] = set()
            for pre_index, pre_value in enumerate(
                require_list(
                    chapter.get("prerequisites", []),
                    f"{chapter_path}.prerequisites",
                )
            ):
                pre_name = require_text(
                    pre_value, f"{chapter_path}.prerequisites[{pre_index}]"
                )
                if pre_name == chapter_name:
                    raise ProjectError(
                        f"{chapter_path}.prerequisites lists the chapter itself: "
                        f"{chapter_name!r}"
                    )
                if pre_name in seen_prerequisites:
                    raise ProjectError(
                        f"{chapter_path}.prerequisites lists {pre_name!r} twice"
                    )
                seen_prerequisites.add(pre_name)
                prerequisite_names.append(pre_name)
            prerequisites_by_name[chapter_name] = prerequisite_names
            prerequisites_by_chapter_id[chapter_id] = [
                f"{category_name}.{pre_name}" for pre_name in prerequisite_names
            ]

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
                    prefix=SOURCE_PREFIXES,
                    must_exist=chapter_id != allow_missing_header_for,
                )
                source_files.add(implementation_header)
                if "source" in implementation:
                    source_files.add(
                        project_path(
                            root,
                            implementation["source"],
                            f"{chapter_path}.implementation.source",
                            prefix=SOURCE_PREFIXES,
                            must_exist=chapter_id != allow_missing_header_for,
                        )
                    )

            chapter_source = implementation_header
            if "source" in chapter:
                chapter_source = project_path(
                    root,
                    chapter["source"],
                    f"{chapter_path}.source",
                    prefix=SOURCE_PREFIXES,
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
                        prefix=SOURCE_PREFIXES,
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
                # 两个独立维度（ADR 0029）：difficulty 只说这个知识点有多难，
                # mastery 只说学完要达到什么程度。难不等于可以跳过，简单也不
                # 等于只需了解，因此两者分别校验、互不推导。
                difficulty = subchapter.get("difficulty", 0)
                if (
                    not isinstance(difficulty, int)
                    or isinstance(difficulty, bool)
                    or not 0 <= difficulty <= 5
                ):
                    raise ProjectError(
                        f"{subchapter_path}.difficulty must be an integer in [0, 5], "
                        f"got {difficulty!r}"
                    )
                knowledge_type = subchapter.get("knowledge_type", "")
                if knowledge_type not in KNOWLEDGE_TYPES:
                    raise ProjectError(
                        f"{subchapter_path}.knowledge_type must be one of "
                        f"{sorted(value for value in KNOWLEDGE_TYPES if value)}, "
                        f"got {knowledge_type!r}"
                    )
                requires_raw = subchapter.get("requires", [])
                require_list(requires_raw, f"{subchapter_path}.requires")
                requires_names: list[str] = []
                for require_index, require_value in enumerate(requires_raw):
                    require_name = require_text(
                        require_value,
                        f"{subchapter_path}.requires[{require_index}]",
                    )
                    if require_name in requires_names:
                        raise ProjectError(
                            f"{subchapter_path}.requires lists {require_name!r} twice"
                        )
                    requires_names.append(require_name)
                mastery_goal = subchapter.get("mastery_goal", "")
                if mastery_goal not in MASTERY_GOALS:
                    raise ProjectError(
                        f"{subchapter_path}.mastery_goal must be one of "
                        f"{sorted(level for level in MASTERY_GOALS if level)}, "
                        f"got {mastery_goal!r}"
                    )
                resolved_source = group_sources.get(group_name, "") or chapter_source
                if "source" in subchapter:
                    resolved_source = project_path(
                        root,
                        subchapter["source"],
                        f"{subchapter_path}.source",
                        prefix=SOURCE_PREFIXES,
                    )
                    source_files.add(resolved_source)

                # 可选：本知识点在哪份手册文档的哪一节被讲到——知识点自己
                # 声明"我在哪一节被讲到"，文档不知道 Athena 存在，不为它
                # 改写一个字符。heading 是否真的存在于该文档由运行时按
                # 标题文本查找，找不到只跳过跳转、不阻断构建（文档处于
                # 频繁重写期时不应逼着开发者同步改配置）。
                teaches = None
                if "teaches" in subchapter:
                    teaches_value = require_object(
                        subchapter["teaches"], f"{subchapter_path}.teaches"
                    )
                    reject_unknown_fields(
                        teaches_value, TEACHES_FIELDS, f"{subchapter_path}.teaches"
                    )
                    teaches_document = project_path(
                        root,
                        teaches_value.get("document"),
                        f"{subchapter_path}.teaches.document",
                        prefix="resources/articles",
                    )
                    if teaches_document not in handbook_document_paths:
                        raise ProjectError(
                            f"{subchapter_path}.teaches.document "
                            f"{teaches_document!r} is not listed in category "
                            f"{category_name}.handbook_documents"
                        )
                    teaches_heading = require_text(
                        teaches_value.get("heading"),
                        f"{subchapter_path}.teaches.heading",
                    )
                    if teaches_document not in headings_by_document:
                        headings_by_document[teaches_document] = (
                            markdown_heading_titles(root / teaches_document)
                        )
                    headings = headings_by_document[teaches_document]
                    heading_count = headings.count(teaches_heading)
                    if heading_count == 0:
                        raise ProjectError(
                            f"{subchapter_path}.teaches.heading "
                            f"{teaches_heading!r} was not found in "
                            f"{teaches_document!r}"
                        )
                    if heading_count > 1:
                        raise ProjectError(
                            f"{subchapter_path}.teaches.heading "
                            f"{teaches_heading!r} is not unique in "
                            f"{teaches_document!r}"
                        )
                    teaches = {
                        "document": teaches_document,
                        "heading": teaches_heading,
                    }

                runtime_subchapter = {
                    "function_id": function_id,
                    "name": method,
                    "title": subchapter_title,
                    "description": subchapter_description,
                    "group": group_name,
                    "source": resolved_source,
                    "difficulty": difficulty,
                    "mastery_goal": mastery_goal,
                    "knowledge_type": knowledge_type,
                    "requires": [],
                    "icon": resolve_icon(
                        own_subchapter_icon,
                        default_subchapter_icon,
                        f"{subchapter_path}.icon",
                    ),
                }
                if teaches is not None:
                    runtime_subchapter["teaches"] = teaches
                runtime_subchapters.append(runtime_subchapter)
                # 同章内可以只写知识点名，跨章必须写完整函数 ID；这里统一展开成
                # 完整 ID，运行时不再需要解析短名。
                expanded_requires = [
                    name if "." in name else f"{chapter_id}.{name}"
                    for name in requires_names
                ]
                requirements_by_id[function_id] = expanded_requires
                requirement_locations[function_id] = subchapter_path
                chapter_of_function[function_id] = chapter_id
                titles_by_function[function_id] = (subchapter_title, chapter_title)
                raw_requirements.append(
                    (function_id, chapter_id, subchapter_path, expanded_requires,
                     runtime_subchapter)
                )

            runtime_learning_units: list[dict] = []
            seen_learning_unit_ids: set[str] = set()
            learning_units = require_list(
                chapter.get("learning_units", []),
                f"{chapter_path}.learning_units",
            )
            if learning_units and not overview_document:
                raise ProjectError(
                    f"{chapter_path}.learning_units requires overview_document"
                )
            if overview_document and overview_document not in headings_by_document:
                headings_by_document[overview_document] = markdown_heading_titles(
                    root / overview_document
                )
            for unit_index, unit_value in enumerate(learning_units):
                unit_path = f"{chapter_path}.learning_units[{unit_index}]"
                unit = require_object(unit_value, unit_path)
                reject_unknown_fields(unit, LEARNING_UNIT_FIELDS, unit_path)
                unit_id = require_text(unit.get("id"), f"{unit_path}.id")
                if not IDENTIFIER_PATTERN.fullmatch(unit_id):
                    raise ProjectError(
                        f"{unit_path}.id must be an ASCII identifier: {unit_id!r}"
                    )
                if unit_id in seen_learning_unit_ids:
                    raise ProjectError(
                        f"duplicate learning unit id in {chapter_id}: {unit_id}"
                    )
                seen_learning_unit_ids.add(unit_id)
                heading = require_text(unit.get("heading"), f"{unit_path}.heading")
                if heading not in headings_by_document[overview_document]:
                    raise ProjectError(
                        f"{unit_path}.heading {heading!r} was not found in "
                        f"{overview_document!r}"
                    )
                choices = require_list(unit.get("choices"), f"{unit_path}.choices")
                if len(choices) < 2:
                    raise ProjectError(f"{unit_path}.choices needs at least two options")
                normalized_choices = [
                    require_text(choice, f"{unit_path}.choices[{choice_index}]")
                    for choice_index, choice in enumerate(choices)
                ]
                correct_choice = unit.get("correct_choice")
                if (
                    not isinstance(correct_choice, int)
                    or isinstance(correct_choice, bool)
                    or not 0 <= correct_choice < len(normalized_choices)
                ):
                    raise ProjectError(
                        f"{unit_path}.correct_choice must index choices"
                    )
                experiment = require_text(
                    unit.get("experiment"), f"{unit_path}.experiment"
                )
                if experiment not in seen_methods:
                    raise ProjectError(
                        f"{unit_path}.experiment must name a subchapter in "
                        f"{chapter_id}: {experiment!r}"
                    )
                runtime_learning_units.append(
                    {
                        "id": unit_id,
                        "heading": heading,
                        "claim": require_text(unit.get("claim"), f"{unit_path}.claim"),
                        "question": require_text(
                            unit.get("question"), f"{unit_path}.question"
                        ),
                        "choices": normalized_choices,
                        "correct_choice": correct_choice,
                        "feedback": require_text(
                            unit.get("feedback"), f"{unit_path}.feedback"
                        ),
                        "follow_up": require_text(
                            unit.get("follow_up"), f"{unit_path}.follow_up"
                        ),
                        "experiment_function_id": f"{chapter_id}.{experiment}",
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
                    "prerequisites": prerequisite_names,
                    "groups": runtime_groups,
                    "subchapters": runtime_subchapters,
                    "learning_units": runtime_learning_units,
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

        validate_prerequisite_graph(prerequisites_by_name, category_name)

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

    # 章节前置的传递闭包：知识点依赖只能指向本章或（传递）前置章节。
    reachable_chapters: dict[str, set[str]] = {}

    def collect_reachable(chapter_id: str, seen: set[str]) -> set[str]:
        if chapter_id in reachable_chapters:
            return reachable_chapters[chapter_id]
        if chapter_id in seen:
            return set()
        seen.add(chapter_id)
        result: set[str] = set()
        for pre_id in prerequisites_by_chapter_id.get(chapter_id, []):
            result.add(pre_id)
            result |= collect_reachable(pre_id, seen)
        reachable_chapters[chapter_id] = result
        return result

    for chapter_id in prerequisites_by_chapter_id:
        collect_reachable(chapter_id, set())

    validate_subchapter_requirements(
        requirements_by_id,
        requirement_locations,
        chapter_of_function,
        reachable_chapters,
    )
    # 运行时直接拿到可显示的标题，界面不必反查 Catalog。
    for function_id, chapter_id, _, expanded_requires, runtime_subchapter in (
        raw_requirements
    ):
        runtime_subchapter["requires"] = [
            {
                "function_id": required_id,
                "title": titles_by_function[required_id][0],
                "chapter_title": titles_by_function[required_id][1],
                "same_chapter": chapter_of_function[required_id] == chapter_id,
            }
            for required_id in expanded_requires
        ]

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
