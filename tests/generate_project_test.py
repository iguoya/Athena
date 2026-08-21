#!/usr/bin/env python3
"""End-to-end smoke test for generate_project.py's five commands."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write(path: Path, content: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run(
    generator: Path,
    root: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(generator),
            "--project-root",
            str(root),
            "--config",
            str(root / "resources" / "athena.json"),
            *arguments,
        ],
        check=check,
        capture_output=True,
        text=True,
    )


def assert_rejected(
    generator: Path,
    root: Path,
    config: dict,
    expected_error: str,
) -> None:
    write(
        root / "resources" / "athena.json",
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
    )
    result = run(generator, root, "check", check=False)
    assert result.returncode != 0
    assert expected_error in result.stderr, result.stderr


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_project_test.py <generate_project.py>")
    generator = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(generator.parent))
    from project_generator.model import (  # pylint: disable=import-outside-toplevel
        CXX20_KEYWORDS,
        ProjectError,
        validate_cpp_identifier,
    )

    for keyword in CXX20_KEYWORDS:
        try:
            validate_cpp_identifier(keyword, "test.name", "generated name")
        except ProjectError:
            continue
        raise AssertionError(f"C++20 keyword was accepted: {keyword}")

    with tempfile.TemporaryDirectory(prefix="athena-generator-") as temporary:
        root = Path(temporary)
        write(root / "resources" / "ui" / "chapters" / "code.blp")
        write(root / "resources" / "window.ui")
        write(root / "resources" / "style.css")
        write(root / "resources" / "article.css")
        write(root / "resources" / "icons" / "tiger.svg", "<svg/>\n")
        config = {
            "format_version": 1,
            "defaults": {
                "chapter_ui": {
                    "code": {"blueprint": "resources/ui/chapters/code.blp"},
                },
                "chapter_icon": {
                    "type": "theme",
                    "name": "view-grid-symbolic",
                },
                "subchapter_icon": {
                    "type": "theme",
                    "name": "media-playback-start-symbolic",
                },
            },
            "categories": [
                {
                    "name": "cpp",
                    "title": "C++",
                    "description": "fixture category",
                    "icon": {
                        "type": "theme",
                        "name": "applications-development-symbolic",
                    },
                    "chapters": [
                        {
                            "name": "Widget",
                            "title": "Widget",
                            "description": "fixture chapter",
                            "implementation": {
                                "header": "language/widget/widget.hpp"
                            },
                            "subchapters": [
                                {
                                    "name": "basics",
                                    "title": "基础",
                                    "description": "fixture method",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        write(
            root / "resources" / "athena.json",
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        )

        first = run(generator, root, "scaffold", "--chapter", "cpp.Widget")
        header = root / "language" / "widget" / "widget.hpp"
        source = root / "language" / "widget" / "widget.cpp"
        assert "created: language/widget/widget.hpp" in first.stdout
        assert header.is_file() and source.is_file()

        sentinel = header.read_text(encoding="utf-8") + "// user implementation\n"
        assert "class Widget" in sentinel
        assert "namespace athena" not in sentinel
        assert "namespace athena" not in source.read_text(encoding="utf-8")
        header.write_text(sentinel, encoding="utf-8")
        second = run(generator, root, "scaffold", "--chapter", "cpp.Widget")
        assert "kept: language/widget/widget.hpp" in second.stdout
        assert header.read_text(encoding="utf-8") == sentinel

        checked = run(generator, root, "check")
        assert "1 implementations" in checked.stdout

        resource_output = root / "build" / "app.gresource.xml"
        resources = run(
            generator,
            root,
            "resources",
            "--output",
            str(resource_output),
        )
        assert "code|resources/ui/chapters/code.blp|code.ui" in resources.stdout
        resource_xml = resource_output.read_text(encoding="utf-8")
        assert "code.ui" in resource_xml
        assert "language/widget/widget.hpp" in resource_xml
        assert '<file alias="tiger.svg">icons/tiger.svg</file>' in resource_xml
        assert "/app/icons/icons" not in resource_xml
        assert 'alias="chapter_catalog.json"' in resource_xml
        assert ">athena.json<" not in resource_xml

        catalog_output = root / "build" / "chapter_catalog.generated.json"
        run(generator, root, "catalog", "--output", str(catalog_output))
        catalog = json.loads(catalog_output.read_text(encoding="utf-8"))
        assert catalog["catalog_version"] == 1
        assert "DO NOT EDIT" in catalog["generated_notice"]
        runtime_chapter = catalog["categories"][0]["chapters"][0]
        assert runtime_chapter["resource_path"] == "/app/chapters/code.ui"
        assert runtime_chapter["widget_name"] == "chapter_page"
        assert runtime_chapter["source"] == "language/widget/widget.hpp"
        assert runtime_chapter["icon"]["name"] == "view-grid-symbolic"
        runtime_point = runtime_chapter["subchapters"][0]
        assert runtime_point["function_id"] == "cpp.Widget.basics"
        assert runtime_point["source"] == "language/widget/widget.hpp"
        assert runtime_point["importance"] == 0
        assert runtime_point["icon"]["name"] == "media-playback-start-symbolic"

        write(root / "language" / "widget" / "chapter.cpp")
        write(root / "language" / "widget" / "group.cpp")
        write(root / "language" / "widget" / "point.cpp")
        source_inheritance = copy.deepcopy(config)
        source_chapter = source_inheritance["categories"][0]["chapters"][0]
        source_chapter["source"] = "language/widget/chapter.cpp"
        source_chapter["groups"] = [
            {
                "name": "ownership",
                "title": "Ownership",
                "description": "fixture group",
                "source": "language/widget/group.cpp",
            }
        ]
        source_chapter["subchapters"][0]["group"] = "ownership"
        write(
            root / "resources" / "athena.json",
            json.dumps(source_inheritance, ensure_ascii=False, indent=2) + "\n",
        )
        run(generator, root, "catalog", "--output", str(catalog_output))
        inherited = json.loads(catalog_output.read_text(encoding="utf-8"))
        inherited_point = inherited["categories"][0]["chapters"][0][
            "subchapters"
        ][0]
        assert inherited_point["source"] == "language/widget/group.cpp"

        source_inheritance["categories"][0]["chapters"][0]["subchapters"][0][
            "source"
        ] = "language/widget/point.cpp"
        write(
            root / "resources" / "athena.json",
            json.dumps(source_inheritance, ensure_ascii=False, indent=2) + "\n",
        )
        run(generator, root, "catalog", "--output", str(catalog_output))
        explicit = json.loads(catalog_output.read_text(encoding="utf-8"))
        explicit_point = explicit["categories"][0]["chapters"][0][
            "subchapters"
        ][0]
        assert explicit_point["source"] == "language/widget/point.cpp"

        write(
            root / "resources" / "athena.json",
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        )

        registry_output = root / "build" / "function_registry.generated.cc"
        run(generator, root, "registry", "--output", str(registry_output))
        registry = registry_output.read_text(encoding="utf-8")
        assert "make_shared<Widget>()" in registry
        assert 'registry.add("cpp.Widget.basics"' in registry
        assert "make_function_id" not in registry

        class_keyword = copy.deepcopy(config)
        class_keyword["categories"][0]["chapters"][0]["name"] = "class"
        assert_rejected(
            generator,
            root,
            class_keyword,
            "athena.json.categories[0].chapters[0].name must not be a C++20 keyword",
        )

        method_keyword = copy.deepcopy(config)
        method_keyword["categories"][0]["chapters"][0]["subchapters"][0][
            "name"
        ] = "co_await"
        assert_rejected(
            generator,
            root,
            method_keyword,
            "subchapters[0].name must not be a C++20 keyword",
        )

        unknown_field = copy.deepcopy(config)
        unknown_field["categories"][0]["chapters"][0]["descripton"] = "typo"
        assert_rejected(
            generator,
            root,
            unknown_field,
            "contains unknown field 'descripton'",
        )

        deprecated_field = copy.deepcopy(config)
        deprecated_field["handbook_documents"] = []
        assert_rejected(
            generator,
            root,
            deprecated_field,
            "athena.json.handbook_documents is deprecated",
        )

        old_version_field = copy.deepcopy(config)
        del old_version_field["format_version"]
        old_version_field["schema"] = 1
        assert_rejected(
            generator,
            root,
            old_version_field,
            "rename this old version field to format_version",
        )

        invalid_importance = copy.deepcopy(config)
        invalid_importance["categories"][0]["chapters"][0]["subchapters"][0][
            "importance"
        ] = 6
        assert_rejected(
            generator,
            root,
            invalid_importance,
            "subchapters[0].importance must be an integer in [0, 5]",
        )

        write(
            root / "resources" / "athena.json",
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        )


if __name__ == "__main__":
    main()
