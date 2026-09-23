#!/usr/bin/env python3
"""把 subjects/cpp 首页学科路线图的全部信息逐字导出成 JSON。

为什么要有这个脚本：那张图的内容手工维护在 subjects/cpp/registry/domain_graph.cc
的 C++ 初始化列表里，是 polaris 技术体系图的原料。原料一旦只存在于别的应用的
源码里，那个应用一改动、一删除，信息就没了；靠人手抄 28 个节点 × 四段文字
外加三十多条依赖理由，必然漏字、漏条。所以用解析器机械提取，提取结果进
版本库，吸收工作再从 JSON 出发（ADR 0055 之后另见 polaris ADR 0009）。

它只解析、不改写内容：字段原样搬，枚举转成小写字符串，相邻字符串字面量按
C++ 的规则拼接。跑一次就够，源文件删掉之后这个脚本会自然失效——那时 JSON
已经是唯一事实来源。

用法：
    python3 subjects/polaris/scripts/extract_cpp_roadmap.py [--check]

    --check 只校验已有 JSON 与源文件一致，不写文件（供 check.py 调用）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

POLARIS_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = POLARIS_ROOT.parent.parent
SOURCE = REPO_ROOT / "subjects" / "cpp" / "registry" / "domain_graph.cc"
TARGET = POLARIS_ROOT / "content" / "absorbed" / "cpp-roadmap.json"

# DomainSpec 的字段顺序，见 subjects/cpp/registry/domain_graph.h。
SPEC_FIELDS = [
    "id", "title", "content", "purpose", "difficulty", "icon",
    "kind", "verify", "priority", "track", "note", "prerequisites", "app_id",
]


class Token:
    """解析出来的一个值：字符串、标识符（枚举 / nullptr / 布尔）或嵌套块。"""

    def __init__(self, kind: str, value):
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:  # 调试用
        return f"Token({self.kind}, {self.value!r})"


def parse_block(text: str, start: int) -> tuple[list[Token], int]:
    """从 text[start] == '{' 开始解析一个花括号块，返回逗号分隔的值列表。

    C++ 的相邻字符串字面量自动拼接，这里照同样规则合并——源文件里每段说明
    都是拆成多行写的，不合并就会得到一堆碎片。
    """
    assert text[start] == "{"
    items: list[Token] = []
    index = start + 1
    pending_string: str | None = None
    pending_identifier: list[str] = []

    def flush() -> None:
        nonlocal pending_string, pending_identifier
        if pending_string is not None:
            items.append(Token("string", pending_string))
            pending_string = None
        elif pending_identifier:
            items.append(Token("identifier", "".join(pending_identifier).strip()))
            pending_identifier = []

    while index < len(text):
        char = text[index]
        if char == "/" and text[index : index + 2] == "//":
            index = text.index("\n", index)
            continue
        if char == '"':
            piece, index = parse_string(text, index)
            pending_string = piece if pending_string is None else pending_string + piece
            continue
        if char == "{":
            flush()
            nested, index = parse_block(text, index)
            items.append(Token("block", nested))
            continue
        if char == "}":
            flush()
            return items, index + 1
        if char == ",":
            flush()
            index += 1
            continue
        if char.isspace():
            index += 1
            continue
        pending_identifier.append(char)
        index += 1

    raise ValueError("花括号没有闭合")


def parse_string(text: str, start: int) -> tuple[str, int]:
    """解析一个 C++ 窄字符串字面量，返回内容与下一个位置。"""
    assert text[start] == '"'
    out: list[str] = []
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            out.append(text[index + 1])
            index += 2
            continue
        if char == '"':
            return "".join(out), index + 1
        out.append(char)
        index += 1
    raise ValueError("字符串没有闭合")


def body_of(text: str, marker: str) -> tuple[list[Token], int]:
    position = text.index(marker)
    brace = text.index("{", position + len(marker) - 1)
    return parse_block(text, brace)


def enum_value(token: Token) -> str:
    """DomainKind::Planned -> planned；VerifyMode::Board -> board。"""
    raw = token.value.split("::")[-1]
    out = []
    for i, char in enumerate(raw):
        # 只在小写后面的大写前断词，否则 AI 会被拆成 a_i。
        if char.isupper() and i > 0 and not raw[i - 1].isupper():
            out.append("_")
        out.append(char.lower())
    return "".join(out)


def id_set(text: str, marker: str) -> list[str]:
    items, _ = body_of(text, marker)
    return [token.value for token in items if token.kind == "string"]


def parse_nodes(text: str) -> list[dict]:
    items, _ = body_of(text, "static const vector<DomainSpec> specs = {")
    nodes = []
    for token in items:
        if token.kind != "block":
            raise ValueError(f"意外的顶层值：{token}")
        node: dict = {}
        values = token.value
        for field, value in zip(SPEC_FIELDS, values):
            if field == "prerequisites":
                prerequisites = []
                for entry in value.value:
                    fields = entry.value
                    prerequisites.append({
                        "id": fields[0].value,
                        "reason": fields[1].value,
                        # 省略第三个参数时默认 strong=true。
                        "strong": len(fields) < 3 or fields[2].value == "true",
                    })
                node[field] = prerequisites
            elif field in {"kind", "verify", "priority", "track"}:
                node[field] = enum_value(value)
            else:
                node[field] = value.value
        node.setdefault("prerequisites", [])
        node["app_id"] = node.get("app_id") or ""
        if node["app_id"] == "nullptr":
            node["app_id"] = ""
        nodes.append(node)
    return nodes


def parse_theory(text: str) -> list[dict]:
    items, _ = body_of(text, "static const vector<TheoryTopic> topics = {")
    topics = []
    for token in items:
        fields = token.value
        topics.append({
            "name": fields[0].value,
            "content": fields[1].value,
            "role": fields[2].value,
        })
    return topics


def extract() -> dict:
    text = SOURCE.read_text(encoding="utf-8")
    electronics = id_set(text, "static const set<string> ids = {")
    nodes = parse_nodes(text)
    # entry_ids() 是第二个同名声明，按出现顺序取。
    second = text.index(
        "static const set<string> ids = {",
        text.index("static const set<string> ids = {") + 1,
    )
    entry_items, _ = parse_block(text, text.index("{", second))
    entries = [token.value for token in entry_items if token.kind == "string"]

    for node in nodes:
        node["side"] = "electronics" if node["id"] in electronics else "computer"
        node["entry"] = node["id"] in entries

    return {
        "source_file": str(SOURCE.relative_to(REPO_ROOT)),
        "note": (
            "subjects/cpp 首页学科路线图的逐字导出，是 polaris 技术体系图的原料。"
            "字段含义见 subjects/cpp/registry/domain_graph.h；kind/verify/priority/"
            "track 由同名枚举转写成小写。不要手改这个文件——它由 "
            "subjects/polaris/scripts/extract_cpp_roadmap.py 生成。"
        ),
        "nodes": nodes,
        "theory": parse_theory(text),
    }


def main(argv: list[str]) -> int:
    data = extract()
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    if "--check" in argv:
        if not TARGET.is_file():
            raise SystemExit(f"缺少 {TARGET.relative_to(REPO_ROOT)}，先跑一次这个脚本。")
        if TARGET.read_text(encoding="utf-8") != rendered:
            raise SystemExit(
                f"{TARGET.relative_to(REPO_ROOT)} 与源文件不一致，重新跑这个脚本。"
            )
        print("原料导出与源文件一致。")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(rendered, encoding="utf-8")

    computer = [n for n in data["nodes"] if n["side"] == "computer"]
    electronics = [n for n in data["nodes"] if n["side"] == "electronics"]
    edges = sum(len(n["prerequisites"]) for n in data["nodes"])
    print(f"导出 {len(data['nodes'])} 个节点："
          f"计算机 {len(computer)}、电子信息 {len(electronics)}")
    print(f"依赖 {edges} 条，理论科目 {len(data['theory'])} 条")
    missing = [
        n["id"] for n in data["nodes"]
        if not (n["content"] and n["purpose"] and n["title"])
    ]
    if missing:
        raise SystemExit(f"这些节点缺正文，解析有问题：{missing}")
    print(f"写入 {TARGET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
