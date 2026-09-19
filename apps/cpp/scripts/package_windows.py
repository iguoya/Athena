#!/usr/bin/env python3
"""Build a relocatable Windows zip and optional MSI from a Meson Athena.exe.

GTK 在 Windows 上按「glib DLL 所在目录的上一级」当 prefix。所以包必须维持
MSYS2 的 bin / lib / share 布局：Athena.exe 和运行库在 bin/，主题、schemas、
GdkPixbuf 加载器在对应的 lib/ 与 share/ 下。换机不需要再装 MSYS2。
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
MESON_PROJECT_PATTERN = re.compile(r"^\s*project\s*\(([^)]*)\)", re.MULTILINE | re.DOTALL)
MESON_VERSION_ARGUMENT = re.compile(r"\bversion:\s*'([^']+)'")
LDD_LINE = re.compile(r"^\s*(\S+)\s+=>\s+(.+)$")

# 开始菜单 / ARP 用的产品 GUID，发版之间保持不变，WiX 才认成同系列升级。
MSI_UPGRADE_CODE = "8F3A1C2E-6B9D-4E71-A5C8-2D4F7E9B1A60"

HELPER_NAMES = (
    "gspawn-win64-helper.exe",
    "gspawn-win64-helper-console.exe",
)


class PackagingError(RuntimeError):
    """A user-facing packaging failure."""


_WINDOWS_PATH_CACHE: dict[str, Path] = {}


def run(
    *arguments: str | Path,
    capture: bool = False,
    check: bool = True,
    cwd: Path | None = None,
    quiet: bool = False,
) -> str:
    command = [str(argument) for argument in arguments]
    if not quiet:
        print("+", " ".join(command))
    try:
        result = subprocess.run(
            command,
            check=check,
            text=True,
            capture_output=capture,
            cwd=cwd,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = ""
        if isinstance(error, subprocess.CalledProcessError):
            detail = (error.stderr or error.stdout or "").strip()
        raise PackagingError(
            f"command failed: {' '.join(command)}" + (f"\n{detail}" if detail else "")
        ) from error
    return result.stdout if capture else ""


def require_tool(name: str, extra_dirs: list[Path] | None = None) -> str:
    path = shutil.which(name)
    if path:
        return path
    for directory in extra_dirs or []:
        for candidate in (directory / name, directory / f"{name}.exe"):
            if candidate.is_file():
                return str(candidate)
    raise PackagingError(f"required tool is unavailable: {name}")


def msys_bin_dirs() -> list[Path]:
    dirs: list[Path] = []
    for key in ("MSYSTEM_PREFIX", "MINGW_PREFIX"):
        value = os.environ.get(key)
        if value:
            dirs.append(Path(value) / "bin")
    dirs.extend(
        (
            Path(r"C:\msys64\ucrt64\bin"),
            Path(r"C:\msys64\usr\bin"),
        )
    )
    return dirs


def read_meson_version(project_root: Path) -> str:
    meson_build = project_root / "meson.build"
    if not meson_build.is_file():
        raise PackagingError(f"meson.build not found: {meson_build}")
    content = meson_build.read_text(encoding="utf-8")
    project_match = MESON_PROJECT_PATTERN.search(content)
    if not project_match:
        raise PackagingError("no project() call found in meson.build")
    version_match = MESON_VERSION_ARGUMENT.search(project_match.group(1))
    if not version_match:
        raise PackagingError("no version: argument found in meson.build project()")
    version = version_match.group(1)
    if not VERSION_PATTERN.fullmatch(version):
        raise PackagingError(
            f"meson.build version must use MAJOR.MINOR.PATCH: {version}"
        )
    return version


def require_amd64() -> None:
    if platform.machine().lower() not in {"amd64", "x86_64"}:
        raise PackagingError("Windows packages are currently produced only for x64")


def gtk_prefix() -> Path:
    pkg_config = require_tool("pkg-config", msys_bin_dirs())
    raw = run(pkg_config, "--variable=prefix", "gtk4", capture=True).strip()
    if not raw:
        raise PackagingError("pkg-config gtk4 prefix is empty")
    prefix = Path(raw)
    if not prefix.is_dir():
        raise PackagingError(f"GTK prefix is not a directory: {prefix}")
    return prefix.resolve()


def with_runtime_path(prefix: Path) -> None:
    """让 ldd / 加载器查询能看见 UCRT64 的 DLL，不依赖调用方是否进过 MSYS2。"""
    bin_dir = str(prefix / "bin")
    current = os.environ.get("PATH", "")
    if bin_dir not in current.split(os.pathsep):
        os.environ["PATH"] = bin_dir + os.pathsep + current


def is_system_library(path: Path) -> bool:
    text = str(path).replace("/", "\\").lower()
    return "\\windows\\" in text or text.startswith("c:\\windows")


def cygpath_windows(raw: str) -> Path:
    """ldd 给出 /ucrt64/bin/foo.dll；MinGW Python 的 Path 不认这种根。"""
    cached = _WINDOWS_PATH_CACHE.get(raw)
    if cached is not None:
        return cached
    candidate = Path(raw)
    if candidate.is_file():
        resolved = candidate.resolve()
        _WINDOWS_PATH_CACHE[raw] = resolved
        return resolved
    converter = shutil.which("cygpath") or str(Path(r"C:\msys64\usr\bin\cygpath.exe"))
    converted = run(converter, "-w", raw, capture=True, quiet=True).strip()
    windows = Path(converted)
    if not windows.is_file():
        raise PackagingError(f"could not resolve {raw} to a Windows path")
    resolved = windows.resolve()
    _WINDOWS_PATH_CACHE[raw] = resolved
    return resolved


def parse_ldd(path: Path, ldd: str) -> list[Path]:
    output = run(ldd, path, capture=True)
    resolved: list[Path] = []
    for line in output.splitlines():
        match = LDD_LINE.match(line.strip())
        if not match:
            continue
        target = match.group(2).strip()
        if target.endswith(")"):
            target = target.rsplit(" (", 1)[0].strip()
        if target == "not found":
            name = match.group(1).lower()
            if name.startswith(("api-ms-win-", "ext-ms-")):
                continue
            raise PackagingError(f"{path.name} is missing dependency {match.group(1)}")
        if "/windows/" in target.lower():
            continue
        candidate = cygpath_windows(target)
        if is_system_library(candidate):
            continue
        resolved.append(candidate)
    return resolved


def collect_runtime_dlls(binary: Path, extra_binaries: list[Path], ldd: str) -> list[Path]:
    pending = [binary.resolve(), *[item.resolve() for item in extra_binaries]]
    seen: set[Path] = set()
    dlls: list[Path] = []
    index = 0
    while index < len(pending):
        current = pending[index]
        index += 1
        if current in seen:
            continue
        seen.add(current)
        for dependency in parse_ldd(current, ldd):
            if dependency in seen:
                continue
            if dependency.suffix.lower() == ".dll":
                dlls.append(dependency)
            pending.append(dependency)
    return dlls


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise PackagingError(f"runtime data not found: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=False)


def write_png_ico(png_path: Path, ico_path: Path) -> None:
    """把一张 PNG 包进 ICO。Vista 之后资源管理器认这种写法。"""
    if not png_path.is_file():
        raise PackagingError(f"application icon not found: {png_path}")
    png = png_path.read_bytes()
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22)
    ico_path.write_bytes(header + entry + png)


def find_license(project_root: Path) -> Path:
    for candidate in (project_root, *project_root.parents):
        license_file = candidate / "LICENSE"
        if license_file.is_file():
            return license_file
    raise PackagingError(f"从 {project_root} 往上找不到 LICENSE")


def rewrite_pixbuf_cache(cache_text: str, loaders_dir: Path) -> str:
    rewritten: list[str] = []
    for line in cache_text.splitlines():
        stripped = line.strip()
        if stripped.startswith('"') and stripped.endswith('"') and ".dll" in stripped.lower():
            name = Path(stripped.strip('"')).name
            rewritten.append(f'"{(loaders_dir / name).as_posix()}"')
        else:
            rewritten.append(line)
    return "\n".join(rewritten) + "\n"


def copy_pixbuf_loaders(prefix: Path, staging: Path) -> list[Path]:
    loader_root = prefix / "lib" / "gdk-pixbuf-2.0"
    if not loader_root.is_dir():
        raise PackagingError(f"GdkPixbuf loader root not found: {loader_root}")
    versions = sorted(path for path in loader_root.iterdir() if path.is_dir())
    if not versions:
        raise PackagingError(f"no GdkPixbuf loader version under {loader_root}")
    source_version = versions[-1]
    source_loaders = source_version / "loaders"
    if not source_loaders.is_dir():
        raise PackagingError(f"GdkPixbuf loaders not found: {source_loaders}")

    destination_version = staging / "lib" / "gdk-pixbuf-2.0" / source_version.name
    destination_loaders = destination_version / "loaders"
    destination_loaders.mkdir(parents=True)
    plugins: list[Path] = []
    for source in sorted(source_loaders.glob("*.dll")):
        destination = destination_loaders / source.name
        shutil.copy2(source, destination)
        plugins.append(destination)

    query = shutil.which("gdk-pixbuf-query-loaders") or shutil.which(
        "gdk-pixbuf-query-loaders.exe"
    )
    if query:
        cache_text = run(query, *[str(path) for path in plugins], capture=True)
    else:
        source_cache = source_version / "loaders.cache"
        if not source_cache.is_file():
            raise PackagingError("gdk-pixbuf-query-loaders and loaders.cache are both missing")
        cache_text = source_cache.read_text(encoding="utf-8")
    # 路径到用户机器上才会确定，先写成占位符，Athena.cmd 启动时再展开。
    (destination_version / "loaders.cache.in").write_text(
        rewrite_pixbuf_cache(cache_text, Path("@LOADER_DIR@")),
        encoding="utf-8",
    )
    return plugins


def copy_gio_modules(prefix: Path, staging: Path) -> list[Path]:
    source = prefix / "lib" / "gio" / "modules"
    if not source.is_dir():
        return []
    destination = staging / "lib" / "gio" / "modules"
    destination.mkdir(parents=True)
    modules: list[Path] = []
    for path in sorted(source.glob("*.dll")):
        target = destination / path.name
        shutil.copy2(path, target)
        modules.append(target)
    return modules


def compile_schemas(prefix: Path, staging: Path) -> None:
    source = prefix / "share" / "glib-2.0" / "schemas"
    if not source.is_dir():
        raise PackagingError(f"GSettings schemas not found: {source}")
    destination = staging / "share" / "glib-2.0" / "schemas"
    copy_tree(source, destination)
    compiler = require_tool("glib-compile-schemas", msys_bin_dirs())
    run(compiler, str(destination))
    if not (destination / "gschemas.compiled").is_file():
        raise PackagingError("glib-compile-schemas did not produce gschemas.compiled")


def copy_share_runtime(prefix: Path, staging: Path, project_root: Path) -> None:
    for relative in (
        Path("share/icons/Adwaita"),
        Path("share/icons/hicolor"),
        Path("share/gtksourceview-5"),
        Path("share/gtk-4.0"),
    ):
        source = prefix / relative
        if source.is_dir():
            copy_tree(source, staging / relative)

    icons_root = project_root / "resources" / "icons"
    for size in ("16x16", "32x32", "64x64", "128x128", "256x256", "512x512", "1024x1024"):
        source = icons_root / size / "apps" / "cn.athena.icon.png"
        if not source.is_file():
            raise PackagingError(f"application icon not found: {source}")
        destination = staging / "share" / "icons" / "hicolor" / size / "apps"
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination / "cn.athena.icon.png")

    fonts = prefix / "etc" / "fonts"
    if fonts.is_dir():
        copy_tree(fonts, staging / "etc" / "fonts")


def write_launcher(staging: Path, version: str) -> None:
    (staging / "expand-pixbuf-cache.ps1").write_text(
        "\n".join(
            (
                "$ErrorActionPreference = 'Stop'",
                "$root = Split-Path -Parent $MyInvocation.MyCommand.Path",
                "$versionRoot = Get-ChildItem -Path (Join-Path $root 'lib\\gdk-pixbuf-2.0') -Directory |",
                "    Select-Object -Last 1",
                "if (-not $versionRoot) { return }",
                "$dir = Join-Path $versionRoot.FullName 'loaders'",
                "$inputCache = Join-Path $versionRoot.FullName 'loaders.cache.in'",
                "$outputCache = Join-Path $versionRoot.FullName 'loaders.cache'",
                "if (-not (Test-Path $inputCache)) { return }",
                "$unix = $dir.Replace('\\', '/')",
                "(Get-Content -Raw $inputCache).Replace('@LOADER_DIR@', $unix) |",
                "    Set-Content -NoNewline $outputCache -Encoding utf8",
                "",
            )
        ),
        encoding="utf-8",
    )
    (staging / "Athena.cmd").write_text(
        "\r\n".join(
            (
                "@echo off",
                "setlocal EnableExtensions",
                'set "ROOT=%~dp0"',
                'if "%ROOT:~-1%"=="\\" set "ROOT=%ROOT:~0,-1%"',
                "set GSK_RENDERER=cairo",
                'set "XDG_DATA_DIRS=%ROOT%\\share"',
                'set "GSETTINGS_SCHEMA_DIR=%ROOT%\\share\\glib-2.0\\schemas"',
                'set "GIO_MODULE_DIR=%ROOT%\\lib\\gio\\modules"',
                'set "FONTCONFIG_PATH=%ROOT%\\etc\\fonts"',
                "set PIXBUF_VER=",
                'for /d %%D in ("%ROOT%\\lib\\gdk-pixbuf-2.0\\*") do set "PIXBUF_VER=%%D"',
                "if defined PIXBUF_VER (",
                '  set "GDK_PIXBUF_MODULEDIR=%PIXBUF_VER%\\loaders"',
                '  set "GDK_PIXBUF_MODULE_FILE=%PIXBUF_VER%\\loaders.cache"',
                ")",
                'powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\\expand-pixbuf-cache.ps1"',
                'start "" /D "%ROOT%\\bin" "%ROOT%\\bin\\Athena.exe" %*',
                "",
            )
        ),
        encoding="ascii",
    )
    (staging / "README.txt").write_text(
        "\n".join(
            (
                f"Athena {version}（Windows x64）",
                "",
                "解压后运行 Athena.cmd，或直接打开 bin\\Athena.exe。",
                "本包自带 GTK4 运行时，不需要再装 MSYS2。",
                "当前没有 Authenticode 签名，SmartScreen 可能提示「未知发布者」。",
                "",
            )
        ),
        encoding="utf-8",
    )


def populate_staging(
    project_root: Path,
    binary: Path,
    staging: Path,
    version: str,
) -> None:
    prefix = gtk_prefix()
    with_runtime_path(prefix)
    ldd = require_tool("ldd", msys_bin_dirs())
    bin_dir = staging / "bin"
    bin_dir.mkdir(parents=True)

    executable = bin_dir / "Athena.exe"
    shutil.copy2(binary, executable)

    helpers: list[Path] = []
    for name in HELPER_NAMES:
        source = prefix / "bin" / name
        if source.is_file():
            destination = bin_dir / name
            shutil.copy2(source, destination)
            helpers.append(destination)

    plugins = copy_pixbuf_loaders(prefix, staging)
    modules = copy_gio_modules(prefix, staging)
    dlls = collect_runtime_dlls(executable, helpers + plugins + modules, ldd)
    for dll in dlls:
        shutil.copy2(dll, bin_dir / dll.name)

    compile_schemas(prefix, staging)
    copy_share_runtime(prefix, staging, project_root)
    write_launcher(staging, version)
    shutil.copy2(find_license(project_root), staging / "LICENSE.txt")
    write_png_ico(
        project_root / "resources" / "icons" / "256x256" / "apps" / "cn.athena.icon.png",
        staging / "Athena.ico",
    )

    if not (bin_dir / "libglib-2.0-0.dll").is_file() and not any(
        path.name.startswith("libglib-2.0") for path in bin_dir.glob("*.dll")
    ):
        raise PackagingError("libglib-2.0 was not collected; the bundle would not start")


def write_zip(staging: Path, output_path: Path) -> None:
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(staging).as_posix())


def windows_path(path: Path) -> str:
    text = str(path.resolve())
    if re.match(r"^/[a-zA-Z]/", text):
        return f"{text[1].upper()}:{text[2:]}".replace("/", "\\")
    return text


def find_wix() -> str | None:
    found = shutil.which("wix")
    if found:
        return found
    homes = [Path.home()]
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        homes.append(Path(userprofile))
    for home in homes:
        candidate = home / ".dotnet" / "tools" / "wix.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def write_wxs(wxs_path: Path, version: str, icon: Path) -> None:
    """WiX 5 的 Files 整树收进 MSI，不必给 Adwaita 的每个图标单独写 Component。"""
    wxs_path.write_text(
        "\n".join(
            (
                '<?xml version="1.0" encoding="utf-8"?>',
                '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">',
                '  <Package Name="Athena" Manufacturer="Athena contributors"',
                f'           Version="{version}" UpgradeCode="{MSI_UPGRADE_CODE}"',
                '           Scope="perMachine">',
                '    <MajorUpgrade DowngradeErrorMessage="A newer version of Athena is already installed." />',
                '    <MediaTemplate EmbedCab="yes" />',
                f'    <Icon Id="AthenaIcon" SourceFile="{xml_escape(windows_path(icon))}" />',
                '    <Property Id="ARPPRODUCTICON" Value="AthenaIcon" />',
                '    <StandardDirectory Id="ProgramFiles64Folder">',
                '      <Directory Id="INSTALLFOLDER" Name="Athena" />',
                "    </StandardDirectory>",
                '    <StandardDirectory Id="ProgramMenuFolder">',
                '      <Component Id="StartMenuShortcut" Guid="*">',
                '        <Shortcut Id="AthenaStartMenu"',
                '                  Name="Athena"',
                '                  Description="C++ learning and practice application"',
                '                  Target="[INSTALLFOLDER]Athena.cmd"',
                '                  WorkingDirectory="INSTALLFOLDER"',
                '                  Icon="AthenaIcon" />',
                '        <RegistryValue Root="HKCU" Key="Software\\Athena\\Athena"',
                '                       Name="installed" Type="integer" Value="1" KeyPath="yes" />',
                "      </Component>",
                "    </StandardDirectory>",
                '    <Feature Id="Main" Title="Athena" Level="1">',
                '      <ComponentRef Id="StartMenuShortcut" />',
                '      <Files Directory="INSTALLFOLDER" Include="!(bindpath.staging)\\**" />',
                "    </Feature>",
                "  </Package>",
                "</Wix>",
                "",
            )
        ),
        encoding="utf-8",
    )


def build_msi(staging: Path, output_path: Path, version: str) -> Path:
    wix = find_wix()
    if wix is None:
        raise PackagingError(
            "wix is not on PATH. 装上它：dotnet tool install --global wix"
        )
    if output_path.exists():
        output_path.unlink()
    with tempfile.TemporaryDirectory(prefix="athena-wix-") as temporary:
        wxs_path = Path(temporary) / "Athena.wxs"
        write_wxs(wxs_path, version, staging / "Athena.ico")
        run(
            wix,
            "build",
            "-arch",
            "x64",
            f"-bindpath:staging={windows_path(staging)}",
            "-o",
            str(output_path),
            str(wxs_path),
        )
    if not output_path.is_file():
        raise PackagingError(f"WiX did not produce {output_path}")
    return output_path


def verify_staging(staging: Path) -> None:
    required = (
        staging / "bin" / "Athena.exe",
        staging / "Athena.cmd",
        staging / "share" / "glib-2.0" / "schemas" / "gschemas.compiled",
        staging / "lib" / "gdk-pixbuf-2.0",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise PackagingError("Windows staging tree is incomplete: " + ", ".join(missing))


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--version",
        help="optional; defaults to the meson.build version and must match it",
    )
    parser.add_argument(
        "--skip-msi",
        action="store_true",
        help="only write the zip; used when WiX is not installed",
    )
    return parser


def main() -> int:
    if sys.platform != "win32":
        raise PackagingError("Windows packaging must run on Windows")
    require_amd64()
    args = make_parser().parse_args()

    project_root = args.project_root.resolve()
    meson_version = read_meson_version(project_root)
    if args.version is None:
        version = meson_version
    elif args.version != meson_version:
        raise PackagingError(
            f"--version {args.version} does not match meson.build version "
            f"{meson_version}; update meson.build and the git tag together"
        )
    else:
        version = meson_version

    binary = args.binary.resolve()
    if not binary.is_file():
        raise PackagingError(f"Athena binary not found: {binary}")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"Athena-{version}-windows-x64.zip"
    msi_path = output_dir / f"Athena-{version}-windows-x64.msi"

    with tempfile.TemporaryDirectory(prefix="athena-windows-package-") as temporary:
        staging = Path(temporary) / "Athena"
        populate_staging(project_root, binary, staging, version)
        verify_staging(staging)
        write_zip(staging, zip_path)
        print(f"Created {zip_path}")
        if not args.skip_msi:
            build_msi(staging, msi_path, version)
            print(f"Created {msi_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PackagingError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
