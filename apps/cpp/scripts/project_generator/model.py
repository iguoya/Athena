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

ROOT_FIELDS = frozenset({"format_version", "defaults", "paths", "categories"})
DEFAULT_FIELDS = frozenset({"chapter_ui", "chapter_icon", "subchapter_icon"})
CHAPTER_UI_FIELDS = frozenset({"code"})
CODE_UI_FIELDS = frozenset({"blueprint"})
CATEGORY_FIELDS = frozenset({"name", "title", "description", "icon", "chapters"})
CHAPTER_FIELDS = frozenset(
    {
        "name",
        "title",
        "description",
        "icon",
        "ui",
        "source",
        "implementation",
        "prerequisites",
        "groups",
        "subchapters",
    }
)
CASE_NAME_PATTERN = re.compile(r"[a-z0-9_]+")
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
        "labs",
        "source_refs",
        "stage",
    }
)
# 内容来源标记（ADR 0054，字段名照仓库 ADR 0043 的统一命名）。
SOURCE_REF_FIELDS = frozenset({"source_id", "relation", "locator", "url", "note"})
# 内容来源：这段内容出自哪。每条 source_refs 至少要有一个。
CONTENT_RELATIONS = frozenset({"verbatim", "quoted", "adapted", "authored"})
# 补充说明：可以有，但顶替不了内容来源。
META_RELATIONS = frozenset({"selection_basis", "see_also"})
# 来源登记表，相对 resources/。
CATALOG_RELPATH = "sources/catalog.json"
# 学习页内容（ADR 0055）。一章一份，文件名就是章节 ID，放 resources/lessons/。
LESSONS_DIRNAME = "lessons"
# 数据驱动学习页的骨架，对所有写了课文的章节通用。
# 文件名要与根控件名对得上：生成器按 stem + "_page" 推 widget_name，
# 所以文件叫 lesson.blp，里面的根控件叫 lesson_page。
DATA_LESSON_BLUEPRINT = "resources/ui/lesson.blp"
# 九种块，全部来自 type_semantics 那一章的实际统计，不是设想出来的。
# 缺什么补什么——写内容时发现某种表达没有对应块，那才是加类型的时机。
LESSON_BLOCK_TYPES = frozenset({
    "lead", "prose", "bullets", "code", "callout",
    "section", "table", "steps", "figure",
    # 练习与即时反馈：quiz 当场检验、predict 先猜再验。讲解里就要有地方
    # 让读者验证自己真的懂了，不能只在章末挂一套题。
    "quiz", "predict",
})
# 每种块的必填字段。callout 的 title 可选（有些提示框只有正文）。
LESSON_BLOCK_REQUIRED = {
    "lead": ("text",),
    "prose": ("text",),
    "bullets": ("items",),
    "code": ("text",),
    "callout": ("kind", "blocks"),
    "section": ("title", "blocks"),
    "table": ("rows",),
    "steps": ("items",),
    "figure": ("id",),
    "quiz": ("text", "items", "answer"),
    "predict": ("text", "items", "answer"),
}
LESSON_BLOCK_FIELDS = frozenset({
    "type", "text", "title", "kind", "caption", "note", "id",
    "items", "head", "rows", "blocks", "answer", "source_refs", "tier",
})
CALLOUT_KINDS = frozenset({"why", "key", "note", "trap", "use"})

# 知识点在整条学习路径上的位置（ADR 0056 第 3 节）。与 difficulty（这个点多难）
# 和 mastery_goal（要学到什么程度）正交，三者不要混用。
STAGES = frozenset({"basic", "intermediate", "advanced"})
PATH_FIELDS = frozenset({"name", "title", "description", "default", "chapters"})
# 一节内部的档位（ADR 0056 第 7 节）：core 必须懂、deeper 遇到坑再回来、
# optional 用到再说。与 stage 不是一回事——stage 说这个知识点在整条路上
# 排第几段，tier 说这一节内部哪里难。
SECTION_TIERS = frozenset({"core", "deeper", "optional"})

# 随堂考核（ADR 0054 第 3 条）：掌握度的唯一来源，取代 AI 现场出题。
# 每题必须能指到出处、必须标出覆盖哪些知识点——否则算不出分组正确率。
CHECKPOINT_FIELDS = frozenset({"intro", "questions"})
CHECKPOINT_ITEM_FIELDS = frozenset({
    "id", "stem", "options", "answer", "explain", "source_refs",
})
# 可编辑骨架案例的字段（ADR 0053）。prompt 是题干——这道实验要验证或解决什么；
# goal 是动手清单——补哪个符号、对照哪段输出。两个都必填：只写「补全 xxx」而
# 看不到认知问题，是 apps/dsa ADR 0003 第 5 条点名要避免的写法。
LAB_FIELDS = frozenset({"case", "prompt", "goal", "hint", "source_refs"})
# 案例骨架的所在目录，相对 resources/。GResource 按 /app/cases/<case>/<file>
# 发布，运行期只从那里读（AGENTS.md「教学内容只从 GResource 读」）。
CASES_DIRNAME = "cases"
# 掌握目标：master 需要精通、required 必须掌握、familiar 一般了解；
# 空串表示尚未评定。只按重要性评定，不看出现频率：用错的代价有多硬、是不是后续内容
# 的地基、能不能靠编译器兜底（ADR 0029）。
MASTERY_GOALS = frozenset({"", "master", "required", "familiar"})
# 知识类型决定该用哪种教学动作（ADR 0031）：concept 概念要正反例辨析，
# skill 程序性技能要示范加变式练习，strategy 条件性知识要情境判断加说明理由。
KNOWLEDGE_TYPES = frozenset({"", "concept", "skill", "strategy"})

# 教学/实践源码允许存放的两个顶层目录，互相平级：cplusplus/ 按 C++ 语言
# 特性拆分知识点，practice/ 收纳自成一体的应用实践项目（比如
# practice/pocket_cube/），不嵌在 cplusplus/ 下面。
SOURCE_PREFIXES = ("cplusplus", "practice")


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


class SourceCatalog:
    """来源登记表，惰性加载（ADR 0054）。

    一条 source_refs 都没有的项目（例如刚 scaffold 出来的骨架）不该被强制要求
    这份文件；一旦要标出处，它就必须存在且条目对得上。
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._entries: dict[str, dict] | None = None

    def __contains__(self, source_id: str) -> bool:
        if self._entries is None:
            self._entries = load_source_catalog(self._root)
        return source_id in self._entries


def load_source_catalog(root: Path) -> dict[str, dict]:
    """读来源登记表（ADR 0054）。没有这份文件就等于没人能核对出处。"""
    path = root / "resources" / CATALOG_RELPATH
    if not path.is_file():
        raise ProjectError(f"missing source catalog: resources/{CATALOG_RELPATH}")
    data = load_json(path)
    entries = require_list(
        data.get("sources"), f"resources/{CATALOG_RELPATH}.sources"
    )
    catalog: dict[str, dict] = {}
    for index, value in enumerate(entries):
        label = f"resources/{CATALOG_RELPATH}.sources[{index}]"
        entry = require_object(value, label)
        source_id = require_text(entry.get("id"), f"{label}.id")
        if source_id in catalog:
            raise ProjectError(f"{label}.id is duplicated: {source_id!r}")
        require_text(entry.get("title"), f"{label}.title")
        require_text(entry.get("url"), f"{label}.url")
        # 实地核对过的日期。没有它，这条来源和凭印象写的没区别。
        require_text(entry.get("checked_on"), f"{label}.checked_on")
        tier = entry.get("tier")
        if tier not in (1, 2):
            raise ProjectError(f"{label}.tier must be 1 or 2, got {tier!r}")
        catalog[source_id] = entry
    return catalog


def validate_source_refs(
    raw: object,
    label: str,
    catalog: SourceCatalog,
) -> list[dict]:
    """校验一处内容的来源标记（ADR 0054）。

    要求与仓库 ADR 0043 一致：指得到、可核对、关系分级、自造要说理由。
    """
    entries = require_list(raw, label)
    refs: list[dict] = []
    has_content_relation = False
    for index, value in enumerate(entries):
        ref_path = f"{label}[{index}]"
        ref = require_object(value, ref_path)
        reject_unknown_fields(ref, SOURCE_REF_FIELDS, ref_path)
        source_id = require_text(ref.get("source_id"), f"{ref_path}.source_id")
        if source_id not in catalog:
            raise ProjectError(
                f"{ref_path}.source_id is not in the catalog: {source_id!r}"
            )
        relation = require_text(ref.get("relation"), f"{ref_path}.relation")
        if relation in CONTENT_RELATIONS:
            has_content_relation = True
        elif relation not in META_RELATIONS:
            raise ProjectError(
                f"{ref_path}.relation must be one of "
                f"{sorted(CONTENT_RELATIONS)} (content) or "
                f"{sorted(META_RELATIONS)} (supplementary), got {relation!r}"
            )
        locator = ref.get("locator", "")
        url = ref.get("url", "")
        note = ref.get("note", "")
        for name, field in (("locator", locator), ("url", url), ("note", note)):
            if not isinstance(field, str):
                raise ProjectError(f"{ref_path}.{name} must be a string")
        # 可核对：要么指到原文的位置，要么给能打开的链接。两个都没有，
        # 这条出处就只是一句话。
        if not locator and not url:
            raise ProjectError(
                f"{ref_path} needs a locator or a url so it can be checked"
            )
        # 自造是例外，要说明为什么现成材料覆盖不到。
        if relation == "authored" and not note:
            raise ProjectError(
                f"{ref_path} is authored but does not say why no existing "
                f"material covers it"
            )
        refs.append(
            {
                "source_id": source_id,
                "relation": relation,
                "locator": locator,
                "url": url,
                "note": note,
            }
        )
    if refs and not has_content_relation:
        raise ProjectError(
            f"{label} has only supplementary relations; at least one content "
            f"source ({sorted(CONTENT_RELATIONS)}) is required"
        )
    return refs


def collect_quiz_answers(block: dict, into: list[int]) -> None:
    """收集一章里所有判分题的正确选项下标，用来查位置分布。"""
    if block.get("type") == "quiz" and isinstance(block.get("answer"), int):
        into.append(block["answer"])
    for child in block.get("blocks", []):
        if isinstance(child, dict):
            collect_quiz_answers(child, into)


def validate_lesson_block(
    value: object, label: str, catalog: SourceCatalog
) -> None:
    """校验一个内容块（ADR 0055）。C++ 侧信任数据，把关全在这里（ADR 0013）。"""
    block = require_object(value, label)
    reject_unknown_fields(block, LESSON_BLOCK_FIELDS, label)
    block_type = require_text(block.get("type"), f"{label}.type")
    if block_type not in LESSON_BLOCK_TYPES:
        raise ProjectError(
            f"{label}.type must be one of {sorted(LESSON_BLOCK_TYPES)}, "
            f"got {block_type!r}"
        )
    for field in LESSON_BLOCK_REQUIRED[block_type]:
        if field not in block:
            raise ProjectError(f"{label} is a {block_type} block and needs {field!r}")

    if block_type == "callout":
        kind = require_text(block.get("kind"), f"{label}.kind")
        if kind not in CALLOUT_KINDS:
            raise ProjectError(
                f"{label}.kind must be one of {sorted(CALLOUT_KINDS)}, got {kind!r}"
            )
    if block_type in ("quiz", "predict"):
        options = require_list(block.get("items"), f"{label}.items")
        if len(options) < 2:
            raise ProjectError(f"{label} needs at least two options")
        answer = block.get("answer")
        if not isinstance(answer, int) or isinstance(answer, bool):
            raise ProjectError(f"{label}.answer must be an integer index")
        if not 0 <= answer < len(options):
            raise ProjectError(
                f"{label}.answer is {answer} but there are {len(options)} options"
            )
        # 解析不是可选项：只说「错了」帮不上忙，读者需要知道自己哪一步想歪了。
        if not block.get("note"):
            raise ProjectError(f"{label} needs a note explaining the answer")
        # 判分题必须能指到出处（ADR 0054）。**题目本身也不许自造**——
        # 「内容依据了规范、题目是我编的」不算有出处，那正是自我发挥。
        # predict 不判分、不计掌握度，不受这条约束。
        if block_type == "quiz":
            if not block.get("source_refs"):
                raise ProjectError(
                    f"{label} is a scored question and needs source_refs "
                    f"pointing at the material it is adapted from"
                )
            validate_source_refs(
                block["source_refs"], f"{label}.source_refs", catalog
            )
    if "tier" in block:
        if block_type != "section":
            raise ProjectError(f"{label}.tier only applies to section blocks")
        tier = require_text(block["tier"], f"{label}.tier")
        if tier not in SECTION_TIERS:
            raise ProjectError(
                f"{label}.tier must be one of {sorted(SECTION_TIERS)}, got {tier!r}"
            )
    if block_type == "table":
        rows = require_list(block.get("rows"), f"{label}.rows")
        head = block.get("head", [])
        require_list(head, f"{label}.head")
        for row_index, row in enumerate(rows):
            cells = require_list(row, f"{label}.rows[{row_index}]")
            # 列数对不上，渲染出来就是错位的表格，而且肉眼很难发现是数据的锅。
            if head and len(cells) != len(head):
                raise ProjectError(
                    f"{label}.rows[{row_index}] has {len(cells)} cells but the "
                    f"header has {len(head)}"
                )
    for field in ("items", "head"):
        if field in block:
            for index, item in enumerate(require_list(block[field], f"{label}.{field}")):
                require_text(item, f"{label}.{field}[{index}]")
    for index, child in enumerate(block.get("blocks", [])):
        validate_lesson_block(child, f"{label}.blocks[{index}]", catalog)


def validate_paths(
    raw: object, label: str, chapter_prerequisites: dict[str, list[str]]
) -> list[dict]:
    """校验学习路线（ADR 0056 第 5 节）。

    路线只决定推荐顺序，先修关系是硬的——把一章排在它的前置之前，学的人一进去
    就会卡住。两条路线覆盖的章节必须一致，否则会出现「某个知识点只在一条路线上
    存在」的悄悄分叉。
    """
    entries = require_list(raw, label)
    if not entries:
        return []
    paths: list[dict] = []
    coverage: dict[str, set[str]] = {}
    default_count = 0
    for index, value in enumerate(entries):
        path_label = f"{label}[{index}]"
        path = require_object(value, path_label)
        reject_unknown_fields(path, PATH_FIELDS, path_label)
        name = require_text(path.get("name"), f"{path_label}.name")
        require_text(path.get("title"), f"{path_label}.title")
        require_text(path.get("description"), f"{path_label}.description")
        if name in coverage:
            raise ProjectError(f"{label} has two paths named {name!r}")
        is_default = path.get("default", False)
        if not isinstance(is_default, bool):
            raise ProjectError(f"{path_label}.default must be a boolean")
        default_count += int(is_default)

        chapters = require_list(path.get("chapters"), f"{path_label}.chapters")
        seen: list[str] = []
        for order, chapter_value in enumerate(chapters):
            chapter_name = require_text(
                chapter_value, f"{path_label}.chapters[{order}]"
            )
            if chapter_name not in chapter_prerequisites:
                raise ProjectError(
                    f"{path_label}.chapters[{order}] is not a chapter in this "
                    f"category: {chapter_name!r}"
                )
            if chapter_name in seen:
                raise ProjectError(
                    f"{path_label} lists {chapter_name!r} twice"
                )
            # 先修必须已经出现过，否则这条路线自己就把人带进死路。
            for required in chapter_prerequisites[chapter_name]:
                if required not in seen:
                    raise ProjectError(
                        f"{path_label} puts {chapter_name!r} before its "
                        f"prerequisite {required!r}"
                    )
            seen.append(chapter_name)
        coverage[name] = set(seen)
        paths.append({"name": name, "title": path["title"],
                      "description": path["description"],
                      "default": is_default, "chapters": seen})

    if default_count != 1:
        raise ProjectError(
            f"{label} must mark exactly one path as default, found {default_count}"
        )
    reference_name, reference = next(iter(coverage.items()))
    for name, covered in coverage.items():
        if covered != reference:
            missing = sorted(reference - covered)
            extra = sorted(covered - reference)
            raise ProjectError(
                f"{label}: path {name!r} does not cover the same chapters as "
                f"{reference_name!r}; missing {missing}, extra {extra}"
            )
    return paths


def validate_checkpoint(
    raw: object, label: str, catalog: SourceCatalog
) -> None:
    """校验一个知识点的随堂考核（ADR 0054 第 3 条）。

    它是掌握度的唯一来源，所以比讲解里的随堂题严格：每题都要有出处，
    题目本身也不许自造。成绩按所在知识点落库，因此不需要再标 covers。
    """
    checkpoint = require_object(raw, label)
    reject_unknown_fields(checkpoint, CHECKPOINT_FIELDS, label)
    require_text(checkpoint.get("intro"), f"{label}.intro")

    questions = require_list(checkpoint.get("questions"), f"{label}.questions")
    if len(questions) < 2:
        # 一道题的对错不该决定长期掌握度，多题才作数（见 checkpoint_view.h）。
        raise ProjectError(f"{label}.questions needs at least two questions")

    seen_ids: set[str] = set()
    answers: list[int] = []
    for index, value in enumerate(questions):
        item_path = f"{label}.questions[{index}]"
        item = require_object(value, item_path)
        reject_unknown_fields(item, CHECKPOINT_ITEM_FIELDS, item_path)
        item_id = require_text(item.get("id"), f"{item_path}.id")
        if item_id in seen_ids:
            raise ProjectError(f"{label} has two questions with id {item_id!r}")
        seen_ids.add(item_id)

        require_text(item.get("stem"), f"{item_path}.stem")
        # 解析不是可选项：只说「错了」帮不上忙。
        require_text(item.get("explain"), f"{item_path}.explain")

        options = require_list(item.get("options"), f"{item_path}.options")
        if len(options) < 2:
            raise ProjectError(f"{item_path} needs at least two options")
        for option_index, option in enumerate(options):
            require_text(option, f"{item_path}.options[{option_index}]")

        answer = item.get("answer")
        if not isinstance(answer, int) or isinstance(answer, bool):
            raise ProjectError(f"{item_path}.answer must be an integer index")
        if not 0 <= answer < len(options):
            raise ProjectError(
                f"{item_path}.answer is {answer} but there are {len(options)} options"
            )
        answers.append(answer)

        # 计入掌握度的题必须有出处，题目本身也不许自造（ADR 0054）。
        if not item.get("source_refs"):
            raise ProjectError(
                f"{item_path} is scored and needs source_refs pointing at the "
                f"material it is adapted from"
            )
        validate_source_refs(item["source_refs"], f"{item_path}.source_refs", catalog)

    if len(answers) >= 4:
        top = max(set(answers), key=answers.count)
        if answers.count(top) / len(answers) > 0.6:
            raise ProjectError(
                f"{label}: {answers.count(top)} of {len(answers)} answers sit at "
                f"option {top}; spread them out so the position cannot be guessed"
            )


def validate_lessons(
    root: Path, function_ids: set[str], catalog: SourceCatalog
) -> set[str]:
    """校验 resources/lessons/ 下的全部课文，返回要打进 GResource 的相对路径。

    约定优于配置：文件存在就加载，章节不必在 athena.json 里再声明一次
    （ADR 0055「新增一章 = 写一份 JSON」）。
    """
    lessons_dir = root / "resources" / LESSONS_DIRNAME
    if not lessons_dir.is_dir():
        return set()

    files: set[str] = set()
    for path in sorted(lessons_dir.glob("*.json")):
        label = f"resources/{LESSONS_DIRNAME}/{path.name}"
        data = load_json(path)
        document = require_object(data, label)
        reject_unknown_fields(
            document, frozenset({"chapter", "outline", "topics"}), label
        )
        chapter_id = require_text(document.get("chapter"), f"{label}.chapter")
        # 文件名就是章节 ID：找课文不必先读一遍文件内容。
        if chapter_id != path.stem:
            raise ProjectError(
                f"{label}.chapter is {chapter_id!r} but the file is named "
                f"{path.stem!r}; they must match"
            )
        quiz_answers: list[int] = []
        # 教学大纲是三层分工的第一层（ADR 0028），必填：只有讲解没有方向，
        # 读者不知道这一章要解决什么、哪里重哪里难。
        if "outline" not in document:
            raise ProjectError(f"{label} has no outline; every chapter needs one")
        outline = require_object(document["outline"], f"{label}.outline")
        reject_unknown_fields(
            outline, frozenset({"topic", "title", "subtitle", "blocks"}),
            f"{label}.outline",
        )
        if require_text(outline.get("topic"), f"{label}.outline.topic") != chapter_id:
            raise ProjectError(
                f"{label}.outline.topic must be the chapter id {chapter_id!r}"
            )
        require_text(outline.get("title"), f"{label}.outline.title")
        for index, block in enumerate(
            require_list(outline.get("blocks"), f"{label}.outline.blocks")
        ):
            validate_lesson_block(block, f"{label}.outline.blocks[{index}]", catalog)
            collect_quiz_answers(block, quiz_answers)

        topics = require_list(document.get("topics"), f"{label}.topics")
        seen: set[str] = set()
        for index, value in enumerate(topics):
            topic_path = f"{label}.topics[{index}]"
            topic = require_object(value, topic_path)
            reject_unknown_fields(
                topic,
                frozenset({"topic", "title", "subtitle", "blocks", "checkpoint"}),
                topic_path,
            )
            # 随堂考核是这个知识点掌握度的唯一来源；没有它就永远停在 0 星。
            if "checkpoint" in topic:
                validate_checkpoint(
                    topic["checkpoint"], f"{topic_path}.checkpoint", catalog
                )
            topic_id = require_text(topic.get("topic"), f"{topic_path}.topic")
            # 指向不存在的知识点，页面就是空的——这类错误要在这里挡住。
            if topic_id not in function_ids:
                raise ProjectError(
                    f"{topic_path}.topic references an unknown knowledge point: "
                    f"{topic_id!r}"
                )
            if topic_id in seen:
                raise ProjectError(f"{label} has two entries for {topic_id!r}")
            seen.add(topic_id)
            require_text(topic.get("title"), f"{topic_path}.title")
            blocks = require_list(topic.get("blocks"), f"{topic_path}.blocks")
            if not blocks:
                raise ProjectError(f"{topic_path}.blocks is empty")
            for block_index, block in enumerate(blocks):
                validate_lesson_block(block, f"{topic_path}.blocks[{block_index}]", catalog)
                collect_quiz_answers(block, quiz_answers)

        # 正确答案不能总在同一个位置：位置能猜出来，这套题就不再检验理解，
        # 而是检验记不记得住位置。题量少时不判（样本太小说明不了什么）。
        if len(quiz_answers) >= 4:
            top = max(set(quiz_answers), key=quiz_answers.count)
            share = quiz_answers.count(top) / len(quiz_answers)
            if share > 0.6:
                raise ProjectError(
                    f"{label}: {quiz_answers.count(top)} of {len(quiz_answers)} "
                    f"quiz answers sit at option {top}; spread them out so the "
                    f"position cannot be guessed"
                )
        files.add(f"{LESSONS_DIRNAME}/{path.name}")
    return files


def validate_labs(
    root: Path,
    raw: object,
    label: str,
    case_files: set[str],
    catalog: SourceCatalog,
) -> list[dict]:
    """校验一个知识点的可编辑骨架案例（ADR 0053），返回运行时形态。

    案例源码是教学内容，随 GResource 分发；这里只认 resources/cases/<case>/，
    校验目录与骨架真的存在，免得配置写错要等到运行期才发现。
    """
    entries = require_list(raw, label)
    labs: list[dict] = []
    seen: set[str] = set()
    for index, value in enumerate(entries):
        lab_path = f"{label}[{index}]"
        lab = require_object(value, lab_path)
        reject_unknown_fields(lab, LAB_FIELDS, lab_path)
        case = require_text(lab.get("case"), f"{lab_path}.case")
        if not CASE_NAME_PATTERN.fullmatch(case):
            raise ProjectError(
                f"{lab_path}.case must be lowercase letters, digits and "
                f"underscores: {case!r}"
            )
        if case in seen:
            raise ProjectError(f"{label} lists case {case!r} twice")
        seen.add(case)

        case_dir = root / "resources" / CASES_DIRNAME / case
        if not case_dir.is_dir():
            raise ProjectError(
                f"{lab_path}.case points at a missing directory: "
                f"resources/{CASES_DIRNAME}/{case}"
            )
        sources = sorted(
            path for path in case_dir.rglob("*")
            if path.is_file() and not path.name.startswith(".")
        )
        if not sources:
            raise ProjectError(
                f"{lab_path}.case directory is empty: "
                f"resources/{CASES_DIRNAME}/{case}"
            )
        # 骨架必须自带驱动（ADR 0053 决策第 3 条）：不改任何一行就能编译运行。
        # 这里只能查到入口在不在——真编译交给本机工具链，那是运行期的事。
        if not any(
            "int main" in path.read_text(encoding="utf-8", errors="replace")
            for path in sources
            if path.suffix in {".cpp", ".cc", ".cxx"}
        ):
            raise ProjectError(
                f"{lab_path}.case has no int main() driver: "
                f"resources/{CASES_DIRNAME}/{case}"
            )
        for path in sources:
            case_files.add(path.relative_to(root / "resources").as_posix())

        labs.append(
            {
                "case": case,
                "prompt": require_text(lab.get("prompt"), f"{lab_path}.prompt"),
                "goal": require_text(lab.get("goal"), f"{lab_path}.goal"),
                "hint": lab.get("hint", ""),
                "source_refs": validate_source_refs(
                    lab.get("source_refs", []), f"{lab_path}.source_refs", catalog
                ),
            }
        )
        if not isinstance(labs[-1]["hint"], str):
            raise ProjectError(f"{lab_path}.hint must be a string")
    return labs


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
        # 既有 cplusplus/ 下按语言特性拆分的教学代码，也有 practice/ 下
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
                "Markdown handbooks were removed (ADR 0034)"
            ),
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
        deprecated={"content": "content types were removed (ADR 0012)"},
    )
    chapter_ui = require_object(
        defaults.get("chapter_ui"), "athena.json.defaults.chapter_ui"
    )
    reject_unknown_fields(
        chapter_ui,
        CHAPTER_UI_FIELDS,
        "athena.json.defaults.chapter_ui",
        deprecated={"article": "article chapters were removed (ADR 0012)"},
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
    source_files: set[str] = set()
    case_files: set[str] = set()
    source_catalog = SourceCatalog(root)
    # 学习路线跨分类校验顺序，需要一份不随分类重置的章节先修表。
    prerequisites_everywhere: dict[str, list[str]] = {}
    lessons_dir = root / "resources" / LESSONS_DIRNAME
    chapters_with_lessons = (
        {path.stem for path in lessons_dir.glob("*.json")}
        if lessons_dir.is_dir()
        else set()
    )
    bindings: list[dict] = []
    chapters_by_id: dict[str, dict] = {}
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
            deprecated={
                "order": "array order is the display order",
                "handbook_documents": (
                    "Markdown handbooks were removed; outlines live in the "
                    "chapter's native .blp (ADR 0034)"
                ),
            },
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
                    "content": "article chapters were removed (ADR 0012)",
                    "document": "Markdown handbooks were removed (ADR 0034)",
                    "overview_document": (
                        "the outline is the native 教学大纲 tab in the "
                        "chapter's .blp, not a Markdown file (ADR 0034)"
                    ),
                    "learning_units": (
                        "learning units are placed by the native lesson page "
                        "itself, not by a Markdown heading (ADR 0034)"
                    ),
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
            prerequisites_everywhere[chapter_name] = prerequisite_names
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
                # 写了课文的章节自动走数据驱动页面（ADR 0055「新增一章 = 写一份
                # JSON」）——作者不必再在配置里声明一次页面类型。显式写了 ui 的
                # 仍然以它为准，type_semantics 那种自定义页面不受影响。
                blueprint = (
                    DATA_LESSON_BLUEPRINT
                    if chapter_id in chapters_with_lessons
                    else default_blueprint
                )
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
                        "teaches": (
                            "Markdown handbooks were removed; the native "
                            "lesson page teaches the point (ADR 0034)"
                        ),
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
                stage = subchapter.get("stage", "")
                if stage and stage not in STAGES:
                    raise ProjectError(
                        f"{subchapter_path}.stage must be one of {sorted(STAGES)}, "
                        f"got {stage!r}"
                    )
                mastery_goal = subchapter.get("mastery_goal", "")
                if mastery_goal not in MASTERY_GOALS:
                    raise ProjectError(
                        f"{subchapter_path}.mastery_goal must be one of "
                        f"{sorted(level for level in MASTERY_GOALS if level)}, "
                        f"got {mastery_goal!r}"
                    )
                labs = validate_labs(
                    root,
                    subchapter.get("labs", []),
                    f"{subchapter_path}.labs",
                    case_files,
                    source_catalog,
                )
                subchapter_sources = validate_source_refs(
                    subchapter.get("source_refs", []),
                    f"{subchapter_path}.source_refs",
                    source_catalog,
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
                    "stage": stage,
                    "labs": labs,
                    "source_refs": subchapter_sources,
                    "requires": [],
                    "icon": resolve_icon(
                        own_subchapter_icon,
                        default_subchapter_icon,
                        f"{subchapter_path}.icon",
                    ),
                }
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

    # 课文引用的知识点必须存在，所以放在全部章节解析完之后校验。
    lesson_files = validate_lessons(
        root, set(titles_by_function), source_catalog
    )
    # 路线放在全部章节解析完之后校验：它要拿章节先修来检查顺序。
    learning_paths = validate_paths(
        config.get("paths", []), "athena.json.paths", prerequisites_everywhere
    )

    return {
        "config": config,
        "runtime_catalog": {
            "catalog_version": 1,
            "categories": runtime_categories,
        },
        "ui": seen_ui,
        "source_files": source_files,
        "case_files": case_files,
        "lesson_files": lesson_files,
        "paths": learning_paths,
        "bindings": bindings,
        "chapters": chapters_by_id,
        "category_count": len(categories),
        "chapter_count": chapter_count,
        "subchapter_count": subchapter_count,
    }
