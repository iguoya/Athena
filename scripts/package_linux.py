#!/usr/bin/env python3
"""Build Ubuntu DEB and AppImage release artifacts from one Meson install tree."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PACKAGE_NAME = "athena"
APP_NAME = "Athena"
DEB_ARCHITECTURE = "amd64"
RUNTIME_DEPENDENCIES = (
    "libgtkmm-4.0-0",
    "libgtksourceview-5-0",
    "libwebkitgtk-6.0-4",
    "libmd4c-html0",
    "libsqlite3-0",
)


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, env=env, check=True)


def project_version(project_root: Path) -> str:
    meson_build = (project_root / "meson.build").read_text(encoding="utf-8")
    match = re.search(r"version:\s*'([^']+)'", meson_build)
    if not match:
        raise RuntimeError("could not read the project version from meson.build")
    return match.group(1)


def require_amd64() -> None:
    if platform.machine() not in {"x86_64", "amd64"}:
        raise RuntimeError("Linux packages are currently produced only for x86_64/amd64")


def verify_build_prefix(build_dir: Path) -> None:
    result = subprocess.run(
        ["meson", "introspect", str(build_dir), "--buildoptions"],
        capture_output=True,
        check=True,
        text=True,
    )
    options = json.loads(result.stdout)
    prefix = next((item["value"] for item in options if item["name"] == "prefix"), None)
    if prefix != "/usr":
        raise RuntimeError(
            f"{build_dir} must be configured with --prefix /usr for Debian packaging (found {prefix!r})"
        )


def install_tree(build_dir: Path, destination: Path) -> None:
    run(["meson", "install", "-C", str(build_dir), "--destdir", str(destination)])
    required_paths = (
        destination / "usr/bin/Athena",
        destination / "usr/share/applications/cn.athena.desktop",
        destination / "usr/share/icons/hicolor/scalable/apps/cn.athena.icon.svg",
    )
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise RuntimeError("Meson install tree is incomplete: " + ", ".join(missing))


def write_debian_control(path: Path, version: str) -> None:
    path.write_text(
        "\n".join(
            (
                f"Package: {PACKAGE_NAME}",
                f"Version: {version}",
                "Section: devel",
                "Priority: optional",
                f"Architecture: {DEB_ARCHITECTURE}",
                "Maintainer: Athena contributors <noreply@github.com>",
                "Depends: " + ", ".join(RUNTIME_DEPENDENCIES),
                "Description: C++ learning and practice application",
                " Athena is a local GTK desktop application for learning and practicing C++.",
                "",
            )
        ),
        encoding="utf-8",
    )


def build_deb(project_root: Path, installed_root: Path, output_dir: Path, version: str) -> Path:
    package_root = installed_root.parent / "deb-root"
    shutil.copytree(installed_root, package_root)

    control_directory = package_root / "DEBIAN"
    control_directory.mkdir()
    write_debian_control(control_directory / "control", version)

    documentation_directory = package_root / "usr/share/doc" / PACKAGE_NAME
    documentation_directory.mkdir(parents=True)
    shutil.copy2(project_root / "LICENSE", documentation_directory / "copyright")
    shutil.copy2(project_root / "CHANGELOG.md", documentation_directory / "changelog")

    output_path = output_dir / f"{PACKAGE_NAME}_{version}_{DEB_ARCHITECTURE}.deb"
    run(["dpkg-deb", "--build", "--root-owner-group", str(package_root), str(output_path)])
    return output_path


def appimage_command(tool: Path) -> list[str]:
    if tool.suffix == ".AppImage":
        return [str(tool), "--appimage-extract-and-run"]
    return [str(tool)]


def build_appimage(
    installed_root: Path,
    output_dir: Path,
    version: str,
    linuxdeploy: Path,
    appimage_runtime: Path,
) -> Path:
    if not linuxdeploy.is_file() or not linuxdeploy.stat().st_mode & 0o111:
        raise RuntimeError(f"linuxdeploy is missing or not executable: {linuxdeploy}")
    if not appimage_runtime.is_file():
        raise RuntimeError(f"AppImage runtime is missing: {appimage_runtime}")

    app_dir = installed_root.parent / "Athena.AppDir"
    shutil.copytree(installed_root / "usr", app_dir / "usr")

    desktop_file = app_dir / "usr/share/applications/cn.athena.desktop"
    icon_file = app_dir / "usr/share/icons/hicolor/scalable/apps/cn.athena.icon.svg"
    root_desktop_file = app_dir / desktop_file.name
    root_icon_file = app_dir / icon_file.name
    shutil.copy2(desktop_file, root_desktop_file)
    shutil.copy2(icon_file, root_icon_file)

    command = appimage_command(linuxdeploy) + [
        "--appdir",
        str(app_dir),
        "--executable",
        str(app_dir / "usr/bin/Athena"),
        "--desktop-file",
        str(root_desktop_file),
        "--icon-file",
        str(root_icon_file),
        "--output",
        "appimage",
    ]
    output_path = output_dir / f"{APP_NAME}-{version}-linux-x86_64.AppImage"
    environment = dict(os.environ)
    environment.update(
        {
            "LINUXDEPLOY_OUTPUT_VERSION": version,
            "LDAI_OUTPUT": str(output_path),
            "LDAI_NO_APPSTREAM": "1",
            "LDAI_RUNTIME_FILE": str(appimage_runtime),
        }
    )
    run(command, env=environment)
    if not output_path.is_file():
        raise RuntimeError(f"linuxdeploy did not create {output_path}")
    return output_path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--build-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--linuxdeploy", required=True, type=Path)
    parser.add_argument("--appimage-runtime", required=True, type=Path)
    parser.add_argument("--version")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    project_root = arguments.project_root.resolve()
    build_dir = arguments.build_dir.resolve()
    output_dir = arguments.output_dir.resolve()
    linuxdeploy = arguments.linuxdeploy.resolve()
    appimage_runtime = arguments.appimage_runtime.resolve()

    require_amd64()
    version = project_version(project_root)
    if arguments.version and arguments.version != version:
        raise RuntimeError(f"requested version {arguments.version} does not match meson.build ({version})")
    if not build_dir.is_dir():
        raise RuntimeError(f"Meson build directory does not exist: {build_dir}")
    verify_build_prefix(build_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="athena-linux-package-") as temporary_directory:
        installed_root = Path(temporary_directory) / "install-root"
        install_tree(build_dir, installed_root)
        deb_path = build_deb(project_root, installed_root, output_dir, version)
        appimage_path = build_appimage(installed_root, output_dir, version, linuxdeploy, appimage_runtime)

    print(f"Created {deb_path}")
    print(f"Created {appimage_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
