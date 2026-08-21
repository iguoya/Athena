#!/usr/bin/env python3
"""Validate Athena and generate build or chapter scaffold artifacts."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from project_generator.catalog import render_catalog
from project_generator.model import ProjectError, build_model
from project_generator.registry import render_registry
from project_generator.resources import blueprint_entries, render_resources
from project_generator.scaffold import scaffold


def write_generated(path: Path, content: str) -> None:
    """Atomically replace a generated file only when its content changed."""
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


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Athena and generate resources, runtime catalog, registry, "
            "or chapter skeletons."
        )
    )
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)

    resources = commands.add_parser("resources", help="generate GResource XML")
    resources.add_argument("--output", type=Path, required=True)
    catalog = commands.add_parser("catalog", help="generate normalized runtime Catalog")
    catalog.add_argument("--output", type=Path, required=True)
    registry = commands.add_parser("registry", help="generate FunctionRegistry C++")
    registry.add_argument("--output", type=Path, required=True)
    commands.add_parser("check", help="validate the project without writing files")
    scaffold_parser = commands.add_parser(
        "scaffold", help="create a code chapter skeleton"
    )
    scaffold_parser.add_argument(
        "--chapter", required=True, metavar="CATEGORY.CHAPTER"
    )
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
        for target_id, blueprint, ui_name in blueprint_entries(model):
            print(f"{target_id}|{blueprint}|{ui_name}")
    elif args.command == "catalog":
        write_generated(args.output, render_catalog(model))
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
