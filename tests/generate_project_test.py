#!/usr/bin/env python3
"""End-to-end smoke test for generate_project.py's four commands."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write(path: Path, content: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run(generator: Path, root: Path, *arguments: str) -> subprocess.CompletedProcess:
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
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_project_test.py <generate_project.py>")
    generator = Path(sys.argv[1]).resolve()

    with tempfile.TemporaryDirectory(prefix="athena-generator-") as temporary:
        root = Path(temporary)
        write(root / "resources" / "ui" / "chapters" / "code.blp")
        write(root / "resources" / "ui" / "chapters" / "article.blp")
        write(root / "resources" / "window.ui")
        write(root / "resources" / "style.css")
        write(root / "resources" / "article.css")
        write(root / "resources" / "icons" / "tiger.svg", "<svg/>\n")
        config = {
            "schema": 1,
            "defaults": {
                "content": "code",
                "chapter_ui": {
                    "code": {"blueprint": "resources/ui/chapters/code.blp"},
                    "article": {"blueprint": "resources/ui/chapters/article.blp"},
                },
            },
            "categories": [
                {
                    "name": "cpp",
                    "title": "C++",
                    "description": "fixture category",
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

        registry_output = root / "build" / "function_registry.generated.cc"
        run(generator, root, "registry", "--output", str(registry_output))
        registry = registry_output.read_text(encoding="utf-8")
        assert "make_shared<Widget>()" in registry
        assert 'make_function_id("cpp", "Widget", "basics")' in registry


if __name__ == "__main__":
    main()
