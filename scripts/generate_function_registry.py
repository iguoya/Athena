#!/usr/bin/env python3
"""Generate FunctionRegistry bindings from resources/athena.json."""

import json
import os
import re
import sys


CATEGORY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_relative_header(project_root, header, chapter_id):
    if not isinstance(header, str) or not header:
        fail(f"implementation.header is required for {chapter_id}")
    normalized = header.replace("\\", "/")
    if os.path.isabs(header) or ".." in normalized.split("/"):
        fail(f"unsafe implementation.header for {chapter_id}: {header!r}")
    if not normalized.startswith("language/"):
        fail(
            f"implementation.header for {chapter_id} must be under language/: "
            f"{header!r}"
        )
    if not os.path.isfile(os.path.join(project_root, normalized)):
        fail(f"implementation header not found for {chapter_id}: {header}")
    return normalized


def collect_bindings(config, project_root):
    default_content = config.get("defaults", {}).get("content", "code")
    bindings = []
    for category in config.get("categories", []):
        category_name = category.get("name", "")
        if not CATEGORY_PATTERN.fullmatch(category_name):
            fail(f"invalid category name: {category_name!r}")

        for chapter in category.get("chapters", []):
            implementation = chapter.get("implementation")
            if implementation is None:
                continue

            chapter_name = chapter.get("name", "")
            chapter_id = f"{category_name}.{chapter_name}"
            if chapter.get("content", default_content) != "code":
                fail(f"only code chapters can declare implementation: {chapter_id}")
            if not IDENTIFIER_PATTERN.fullmatch(chapter_name):
                fail(f"invalid class name for {chapter_id}: {chapter_name!r}")
            if not isinstance(implementation, dict):
                fail(f"implementation must be an object for {chapter_id}")

            header = validate_relative_header(
                project_root,
                implementation.get("header"),
                chapter_id,
            )
            methods = []
            for subchapter in chapter.get("subchapters", []):
                method = subchapter.get("name", "")
                if not IDENTIFIER_PATTERN.fullmatch(method):
                    fail(f"invalid method name for {chapter_id}: {method!r}")
                methods.append(method)
            if not methods:
                fail(f"implemented chapter has no subchapters: {chapter_id}")

            bindings.append(
                {
                    "category": category_name,
                    "chapter": chapter_name,
                    "header": header,
                    "methods": methods,
                }
            )
    return bindings


def render(bindings):
    headers = sorted({binding["header"] for binding in bindings})
    lines = [
        "// Generated from resources/athena.json. DO NOT EDIT.",
        '#include "registry/function_registry.h"',
        "",
    ]
    lines.extend(f'#include "{header}"' for header in headers)
    lines.extend(["", "#include <memory>", "", "using namespace std;", ""])
    lines.append("FunctionRegistry create_default_function_registry() {")
    lines.append("    FunctionRegistry registry;")

    for binding in bindings:
        category = binding["category"]
        chapter = binding["chapter"]
        variable = f"{category}_{chapter}".lower()
        class_name = f"athena::{category}::{chapter}"
        lines.append(
            f"    auto {variable} = make_shared<{class_name}>();"
        )
        for method in binding["methods"]:
            lines.append(
                "    registry.add("
                f'make_function_id("{category}", "{chapter}", "{method}"), '
                f"[{variable}](ostream& output) {{"
            )
            lines.append(f"        {variable}->{method}(output);")
            lines.append("    });")
        lines.append("")

    lines.extend(["    return registry;", "}", ""])
    return "\n".join(lines)


def main():
    if len(sys.argv) != 4:
        fail(
            "usage: generate_function_registry.py "
            "<athena.json> <project_root> <output.cc>"
        )

    json_path, project_root, output_path = sys.argv[1:]
    with open(json_path, "r", encoding="utf-8") as source:
        config = json.load(source)
    if config.get("schema") != 1:
        fail(f"unsupported athena.json schema: {config.get('schema')!r}")

    generated = render(collect_bindings(config, project_root))
    with open(output_path, "w", encoding="utf-8", newline="\n") as output:
        output.write(generated)


if __name__ == "__main__":
    main()
