"""Create a chapter's initial implementation without overwriting user files."""

from pathlib import Path

from .model import ProjectError, project_path


def cpp_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def write_new(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
    except FileExistsError:
        return False
    return True


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
    class_name = chapter["name"]

    header_lines = [
        "#pragma once",
        "",
        "#include <iosfwd>",
        "",
        "using namespace std;",
        "",
        f"class {class_name} {{",
        "public:",
    ]
    header_lines.extend(
        f"    void {method}(ostream& output);" for method in chapter["methods"]
    )
    header_lines.extend(["};", ""])

    source_lines = [
        f'#include "{Path(header_rel).name}"',
        "",
        "#include <ostream>",
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
    for path, content in (
        (header_path, "\n".join(header_lines)),
        (source_path, "\n".join(source_lines)),
    ):
        action = "created" if write_new(path, content) else "kept"
        print(f"{action}: {path.relative_to(root)}")
