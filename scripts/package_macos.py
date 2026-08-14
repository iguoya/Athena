#!/usr/bin/env python3
"""Build an unsigned, relocatable Athena.app and DMG from a Meson binary."""

from __future__ import annotations

import argparse
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SYSTEM_PREFIXES = ("/System/", "/usr/lib/")
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class PackagingError(RuntimeError):
    """A user-facing packaging failure."""


def run(*arguments: str | Path, capture: bool = False) -> str:
    command = [str(argument) for argument in arguments]
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=capture,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = ""
        if isinstance(error, subprocess.CalledProcessError):
            detail = (error.stderr or error.stdout or "").strip()
        raise PackagingError(
            f"command failed: {' '.join(command)}" + (f"\n{detail}" if detail else "")
        ) from error
    return result.stdout if capture else ""


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise PackagingError(f"required tool is unavailable: {name}")
    return path


def brew_prefix() -> Path:
    return Path(run(require_tool("brew"), "--prefix", capture=True).strip())


def architecture_name() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    raise PackagingError(f"unsupported macOS architecture: {machine}")


def dylib_dependencies(path: Path) -> list[str]:
    output = run(require_tool("otool"), "-L", path, capture=True)
    dependencies = []
    for line in output.splitlines()[1:]:
        value = line.strip().split(" (compatibility version", 1)[0]
        if value:
            dependencies.append(value)
    return dependencies


def is_external_library(value: str) -> bool:
    return value.startswith("/") and not value.startswith(SYSTEM_PREFIXES)


def copy_runtime_libraries(
    executable: Path,
    plugins: list[Path],
    frameworks_dir: Path,
) -> list[Path]:
    frameworks_dir.mkdir(parents=True, exist_ok=True)
    targets = [executable, *plugins]
    scanned: set[Path] = set()
    source_by_name: dict[str, Path] = {}
    copied_libraries: list[Path] = []
    rewrites: dict[Path, list[tuple[str, str]]] = {}

    index = 0
    while index < len(targets):
        target = targets[index]
        index += 1
        if target in scanned:
            continue
        scanned.add(target)

        for dependency in dylib_dependencies(target):
            if not is_external_library(dependency):
                continue
            source = Path(dependency).resolve()
            if not source.is_file():
                raise PackagingError(f"dynamic library not found: {dependency}")
            name = source.name
            previous = source_by_name.get(name)
            if previous and previous != source:
                raise PackagingError(
                    f"dynamic library name collision: {previous} and {source}"
                )
            source_by_name[name] = source
            destination = frameworks_dir / name
            if not destination.exists():
                shutil.copy2(source, destination)
                copied_libraries.append(destination)
                targets.append(destination)
            replacement = f"@executable_path/../Frameworks/{name}"
            rewrites.setdefault(target, []).append((dependency, replacement))

    install_name_tool = require_tool("install_name_tool")
    for target, changes in rewrites.items():
        for original, replacement in changes:
            run(install_name_tool, "-change", original, replacement, target)
    for library in copied_libraries:
        run(
            install_name_tool,
            "-id",
            f"@executable_path/../Frameworks/{library.name}",
            library,
        )
    framework_names = {library.name for library in copied_libraries}
    for target in targets:
        for dependency in dylib_dependencies(target):
            if dependency.startswith("@rpath/"):
                name = Path(dependency).name
                if name in framework_names:
                    run(
                        install_name_tool,
                        "-change",
                        dependency,
                        f"@executable_path/../Frameworks/{name}",
                        target,
                    )
    for plugin in plugins:
        if plugin.suffix == ".dylib":
            run(install_name_tool, "-id", f"@loader_path/{plugin.name}", plugin)
    return copied_libraries


def copy_gtk_runtime(resources_dir: Path, homebrew_prefix: Path) -> list[Path]:
    share_dir = resources_dir / "share"
    for relative in (
        Path("icons/Adwaita"),
        Path("icons/hicolor"),
        Path("glib-2.0/schemas"),
    ):
        source = homebrew_prefix / "share" / relative
        if not source.is_dir():
            raise PackagingError(f"GTK runtime data not found: {source}")
        shutil.copytree(source, share_dir / relative, symlinks=False)

    fonts_source = homebrew_prefix / "etc" / "fonts"
    if fonts_source.is_dir():
        shutil.copytree(fonts_source, resources_dir / "etc" / "fonts", symlinks=False)

    loader_root = homebrew_prefix / "lib" / "gdk-pixbuf-2.0" / "2.10.0"
    loader_cache = loader_root / "loaders.cache"
    loaders_dir = loader_root / "loaders"
    if not loader_cache.is_file() or not loaders_dir.is_dir():
        raise PackagingError(f"GdkPixbuf loader data not found under {loader_root}")

    bundled_loader_dir = (
        resources_dir / "lib" / "gdk-pixbuf-2.0" / "2.10.0" / "loaders"
    )
    bundled_loader_dir.mkdir(parents=True)
    cache_lines = []
    plugins: list[Path] = []
    module_pattern = re.compile(r'^"([^"]+)"$')
    for line in loader_cache.read_text(encoding="utf-8").splitlines():
        match = module_pattern.match(line)
        if not match:
            cache_lines.append(line)
            continue
        source = Path(match.group(1)).resolve()
        if not source.is_file():
            raise PackagingError(f"GdkPixbuf loader not found: {source}")
        destination = bundled_loader_dir / source.name
        if not destination.exists():
            shutil.copy2(source, destination)
            plugins.append(destination)
        cache_lines.append(f'"@LOADER_DIR@/{destination.name}"')

    cache_output = bundled_loader_dir.parent / "loaders.cache.in"
    cache_output.write_text("\n".join(cache_lines) + "\n", encoding="utf-8")
    return plugins


def create_icon(project_root: Path, resources_dir: Path) -> None:
    source = project_root / "resources" / "icons" / "tiger.svg"
    if not source.is_file():
        raise PackagingError(f"application icon source not found: {source}")
    rsvg_convert = require_tool("rsvg-convert")
    iconutil = require_tool("iconutil")
    with tempfile.TemporaryDirectory(prefix="athena-icon-") as temporary:
        iconset = Path(temporary) / "Athena.iconset"
        iconset.mkdir()
        sizes = {
            "icon_16x16.png": 16,
            "icon_16x16@2x.png": 32,
            "icon_32x32.png": 32,
            "icon_32x32@2x.png": 64,
            "icon_128x128.png": 128,
            "icon_128x128@2x.png": 256,
            "icon_256x256.png": 256,
            "icon_256x256@2x.png": 512,
            "icon_512x512.png": 512,
            "icon_512x512@2x.png": 1024,
        }
        for filename, size in sizes.items():
            run(
                rsvg_convert,
                "--width",
                str(size),
                "--height",
                str(size),
                "--output",
                iconset / filename,
                source,
            )
        run(iconutil, "--convert", "icns", iconset, "--output", resources_dir / "Athena.icns")


def render_templates(project_root: Path, contents_dir: Path, version: str) -> None:
    template_dir = project_root / "packaging" / "macos"
    plist_template = (template_dir / "Info.plist.in").read_text(encoding="utf-8")
    plist_path = contents_dir / "Info.plist"
    plist_path.write_text(plist_template.replace("@VERSION@", version), encoding="utf-8")
    with plist_path.open("rb") as source:
        plistlib.load(source)

    launcher = contents_dir / "MacOS" / "Athena"
    shutil.copy2(template_dir / "Athena.in", launcher)
    launcher.chmod(0o755)


def verify_bundle(app_path: Path) -> None:
    forbidden = ("/usr/local/", "/opt/homebrew/")
    macho_files = [app_path / "Contents" / "MacOS" / "Athena-bin"]
    macho_files.extend((app_path / "Contents" / "Frameworks").glob("*"))
    macho_files.extend(
        (app_path / "Contents" / "Resources" / "lib").rglob("*.so")
    )
    macho_files.extend(
        (app_path / "Contents" / "Resources" / "lib").rglob("*.dylib")
    )
    for path in macho_files:
        for dependency in dylib_dependencies(path):
            if dependency.startswith(forbidden):
                raise PackagingError(
                    f"bundle still references Homebrew path: {path}: {dependency}"
                )


def ad_hoc_sign(app_path: Path) -> None:
    codesign = require_tool("codesign")
    nested = list((app_path / "Contents" / "Frameworks").glob("*"))
    nested.extend((app_path / "Contents" / "Resources" / "lib").rglob("*.so"))
    nested.extend((app_path / "Contents" / "Resources" / "lib").rglob("*.dylib"))
    nested.append(app_path / "Contents" / "MacOS" / "Athena-bin")
    for path in nested:
        run(codesign, "--force", "--sign", "-", path)
    run(codesign, "--force", "--sign", "-", app_path)
    run(codesign, "--verify", "--deep", "--strict", app_path)


def create_dmg(app_path: Path, output_path: Path) -> None:
    hdiutil = require_tool("hdiutil")
    with tempfile.TemporaryDirectory(prefix="athena-dmg-") as temporary:
        staging = Path(temporary)
        shutil.copytree(app_path, staging / app_path.name, symlinks=True)
        os.symlink("/Applications", staging / "Applications")
        run(
            hdiutil,
            "create",
            "-volname",
            "Athena",
            "-srcfolder",
            staging,
            "-ov",
            "-format",
            "UDZO",
            output_path,
        )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    return parser


def main() -> int:
    if sys.platform != "darwin":
        raise PackagingError("macOS packaging must run on macOS")
    args = make_parser().parse_args()
    if not VERSION_PATTERN.fullmatch(args.version):
        raise PackagingError(f"version must use MAJOR.MINOR.PATCH: {args.version}")

    project_root = args.project_root.resolve()
    binary = args.binary.resolve()
    output_dir = args.output_dir.resolve()
    if not binary.is_file():
        raise PackagingError(f"Athena binary not found: {binary}")
    output_dir.mkdir(parents=True, exist_ok=True)

    architecture = architecture_name()
    app_path = output_dir / "Athena.app"
    dmg_path = output_dir / f"Athena-{args.version}-macos-{architecture}.dmg"
    if app_path.exists():
        shutil.rmtree(app_path)
    if dmg_path.exists():
        dmg_path.unlink()

    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    frameworks_dir = contents_dir / "Frameworks"
    resources_dir = contents_dir / "Resources"
    for directory in (macos_dir, frameworks_dir, resources_dir):
        directory.mkdir(parents=True)

    executable = macos_dir / "Athena-bin"
    shutil.copy2(binary, executable)
    executable.chmod(0o755)
    render_templates(project_root, contents_dir, args.version)
    create_icon(project_root, resources_dir)
    plugins = copy_gtk_runtime(resources_dir, brew_prefix())
    libraries = copy_runtime_libraries(executable, plugins, frameworks_dir)
    verify_bundle(app_path)
    ad_hoc_sign(app_path)
    create_dmg(app_path, dmg_path)

    print(f"Created {app_path}")
    print(f"Bundled {len(libraries)} dynamic libraries and {len(plugins)} image loaders")
    print(f"Created {dmg_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PackagingError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
