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
MESON_PROJECT_PATTERN = re.compile(r"^\s*project\s*\(([^)]*)\)", re.MULTILINE | re.DOTALL)
MESON_VERSION_ARGUMENT = re.compile(r"\bversion:\s*'([^']+)'")


class PackagingError(RuntimeError):
    """A user-facing packaging failure."""


def run(*arguments: str | Path, capture: bool = False, check: bool = True) -> str:
    command = [str(argument) for argument in arguments]
    try:
        result = subprocess.run(
            command,
            check=check,
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


def require_tool(name: str, *, formula: str | None = None) -> str:
    """找一个外部工具；formula 给出它所属的 Homebrew 包名时可以绕过未 link。

    Homebrew 的包没有 brew link（keg-only、被 unlink、或安装时跳过）时，
    它的 bin 不在 PATH 里，shutil.which 就找不到——但包本身是装好的。
    这种情况下直接去它自己的 bin 找，比让打包失败要合理：装了就该能用。
    """
    path = shutil.which(name)
    if path:
        return path
    if formula:
        formula_prefix = brew_formula_prefix(formula)
        if formula_prefix:
            candidate = formula_prefix / "bin" / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
        raise PackagingError(
            f"required tool is unavailable: {name}. "
            f"装上它：brew install {formula}；"
            f"已经装了却找不到，多半是没 link：brew link {formula}"
        )
    raise PackagingError(f"required tool is unavailable: {name}")


def brew_prefix() -> Path:
    return Path(run(require_tool("brew"), "--prefix", capture=True).strip())


def brew_formula_prefix(formula: str) -> Path | None:
    try:
        value = run(require_tool("brew"), "--prefix", formula, capture=True).strip()
    except PackagingError:
        return None
    return Path(value) if value else None


def homebrew_runtime_path(
    homebrew_prefix: Path,
    formula: str,
    relative: Path,
    *,
    directory: bool = True,
) -> Path:
    candidates = [homebrew_prefix / relative]
    formula_prefix = brew_formula_prefix(formula)
    if formula_prefix:
        candidates.append(formula_prefix / relative)

    predicate = Path.is_dir if directory else Path.is_file
    for candidate in candidates:
        if predicate(candidate):
            return candidate
    locations = ", ".join(str(candidate) for candidate in candidates)
    raise PackagingError(f"Homebrew runtime data not found: {locations}")


def architecture_name() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    raise PackagingError(f"unsupported macOS architecture: {machine}")


def read_meson_version(project_root: Path) -> str:
    """Read the project() version from meson.build, the single version source."""
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


def dylib_dependencies(path: Path) -> list[str]:
    output = run(require_tool("otool"), "-L", path, capture=True)
    dependencies = []
    for line in output.splitlines()[1:]:
        value = line.strip().split(" (compatibility version", 1)[0]
        if value:
            dependencies.append(value)
    return dependencies


def rpath_entries(path: Path) -> list[str]:
    """读二进制的 LC_RPATH 列表。"""
    output = run(require_tool("otool"), "-l", path, capture=True)
    entries: list[str] = []
    lines = output.splitlines()
    for index, line in enumerate(lines):
        if "cmd LC_RPATH" not in line:
            continue
        for follow in lines[index : index + 4]:
            stripped = follow.strip()
            if stripped.startswith("path "):
                entries.append(stripped[len("path ") :].split(" (offset")[0])
                break
    return entries


def homebrew_library_search_paths(prefix: Path) -> list[str]:
    """Homebrew 里所有包的 lib 目录。

    没有 brew link 的包（keg-only 或被 unlink）不会出现在 <prefix>/lib 下，
    但 <prefix>/opt/<formula> 这个软链 brew 总会建。librsvg 就是这种情况：
    它只被 GdkPixbuf 的 SVG loader 依赖，主程序的 rpath 里没有它的 Cellar
    路径，只按可执行文件的 rpath 去找必然落空。
    """
    paths = [str(prefix / "lib")]
    opt = prefix / "opt"
    if opt.is_dir():
        paths.extend(
            str(formula / "lib")
            for formula in sorted(opt.iterdir())
            if (formula / "lib").is_dir()
        )
    return paths


def resolve_rpath_dependency(dependency: str, search_paths: list[str]) -> Path | None:
    """把 @rpath/libfoo.dylib 解析成真实文件。

    构建期的 LC_RPATH 指向 Homebrew 的 Cellar 目录，@rpath/ 依赖就是在那里
    找到的。不解析它们的后果不是"漏打一个库"那么轻——bundle 里留着
    @rpath/librsvg-2.2.dylib，dyld 会顺着可执行文件残留的 Homebrew rpath 去
    系统里加载那一份，于是同一个进程里出现两份 libgio，GType 互相抢注，
    librsvg 的 is_input_stream() 断言随机失败，SVG 插图时有时无。
    """
    name = Path(dependency).name
    for base in search_paths:
        if base.startswith("@"):
            continue
        candidate = Path(base) / name
        if candidate.is_file():
            return candidate.resolve()
    return None


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
    # 构建期的 rpath 是 @rpath/ 依赖的主要来源；再补上 Homebrew 各包自己的
    # lib 目录，否则只被插件依赖、又没 brew link 的库（librsvg）解析不出来。
    search_paths = rpath_entries(executable) + homebrew_library_search_paths(
        brew_prefix()
    )

    index = 0
    while index < len(targets):
        target = targets[index]
        index += 1
        if target in scanned:
            continue
        scanned.add(target)

        for dependency in dylib_dependencies(target):
            if dependency.startswith("@rpath/"):
                resolved = resolve_rpath_dependency(dependency, search_paths)
                if resolved is None:
                    continue
                source = resolved
            elif is_external_library(dependency):
                source = Path(dependency).resolve()
            else:
                continue
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
    framework_names = {path.name for path in frameworks_dir.glob("*.dylib")}
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

    # 删掉构建期留下的 Homebrew LC_RPATH。只要它们还在，dyld 解析任何没改写
    # 干净的 @rpath/ 依赖时就会落到系统库上，于是同一进程加载两份 libgio、
    # GType 互相抢注，SVG 插图时有时无。删掉之后这类遗漏会变成明确的加载
    # 失败，而不是随机的静默错误。
    for target in [*targets, *copied_libraries]:
        for entry in rpath_entries(target):
            if entry.startswith("@"):
                continue
            run(install_name_tool, "-delete_rpath", entry, target, check=False)

    # 收尾自检：删掉 Homebrew rpath 之后，任何残留的 @rpath/ 引用都再也解析
    # 不到了，dlopen 会失败。这类失败是静默的——GdkPixbuf 加载不到 SVG loader
    # 只会让图片显示不出来，不报错、不崩溃，光看构建日志根本发现不了。宁可在
    # 这里把包打失败。
    unresolved = [
        (target, dependency)
        for target in [*targets, *copied_libraries]
        for dependency in dylib_dependencies(target)
        if dependency.startswith("@rpath/")
    ]
    if unresolved:
        detail = "; ".join(
            f"{target.name} -> {dependency}" for target, dependency in unresolved
        )
        raise PackagingError(
            "bundle 内存在无法解析的 @rpath 依赖，运行时 dlopen 会静默失败："
            f"{detail}"
        )
    return copied_libraries


def copy_gtk_runtime(resources_dir: Path, homebrew_prefix: Path) -> list[Path]:
    for formula, relative in (
        ("adwaita-icon-theme", Path("share/icons/Adwaita")),
        ("hicolor-icon-theme", Path("share/icons/hicolor")),
        ("glib", Path("share/glib-2.0/schemas")),
    ):
        source = homebrew_runtime_path(homebrew_prefix, formula, relative)
        destination = resources_dir / relative
        shutil.copytree(source, destination, symlinks=False)

    try:
        fonts_source = homebrew_runtime_path(
            homebrew_prefix, "fontconfig", Path("etc/fonts")
        )
    except PackagingError:
        fonts_source = None
    if fonts_source:
        shutil.copytree(fonts_source, resources_dir / "etc" / "fonts", symlinks=False)

    loader_relative = Path("lib/gdk-pixbuf-2.0/2.10.0")
    loader_root = homebrew_runtime_path(
        homebrew_prefix, "gdk-pixbuf", loader_relative
    )
    loader_cache = homebrew_runtime_path(
        homebrew_prefix,
        "gdk-pixbuf",
        loader_relative / "loaders.cache",
        directory=False,
    )
    loaders_dir = loader_root / "loaders"
    if not loaders_dir.is_dir():
        raise PackagingError(f"GdkPixbuf loaders not found under {loader_root}")

    bundled_loader_dir = (
        resources_dir / "lib" / "gdk-pixbuf-2.0" / "2.10.0" / "loaders"
    )
    bundled_loader_dir.mkdir(parents=True)
    plugins: list[Path] = []
    module_pattern = re.compile(r'^"([^"]+)"$')

    # loaders.cache 是"模块路径行 + 若干描述行"的块，块之间以空行分隔。按块处理
    # 而不是按行：cache 记着某个 loader 而文件不在时（提供它的包没 link，最常见
    # 的就是 librsvg），要把整块丢掉，只删模块路径行会留下孤立的描述行。
    #
    # ADR 0038 之后应用自己不再加载任何 SVG，所以缺 SVG loader 不再是打包的
    # 硬错误——跳过它，打出来的包一样能跑。
    kept_blocks: list[str] = []
    skipped: list[str] = []
    for block in loader_cache.read_text(encoding="utf-8").split("\n\n"):
        lines = block.splitlines()
        module_index = next(
            (index for index, line in enumerate(lines)
             if module_pattern.match(line)),
            None,
        )
        if module_index is None:
            kept_blocks.append(block)
            continue
        source = Path(
            module_pattern.match(lines[module_index]).group(1)
        ).resolve()
        if not source.is_file():
            skipped.append(source.name)
            continue
        destination = bundled_loader_dir / source.name
        if not destination.exists():
            shutil.copy2(source, destination)
            plugins.append(destination)
        lines[module_index] = f'"@LOADER_DIR@/{destination.name}"'
        kept_blocks.append("\n".join(lines))
    if skipped:
        print(f"Skipped missing GdkPixbuf loaders: {', '.join(sorted(skipped))}")
    cache_lines = "\n\n".join(kept_blocks).splitlines()

    cache_output = bundled_loader_dir.parent / "loaders.cache.in"
    cache_output.write_text("\n".join(cache_lines) + "\n", encoding="utf-8")
    return plugins


def create_icon(project_root: Path, resources_dir: Path) -> None:
    # 图标源是仓库里的 PNG 尺寸集（ADR 0038：不再依赖 SVG 渲染）。以前这里用
    # rsvg-convert 现场把 SVG 渲染成各个尺寸，打包因此要求开发机装着 librsvg；
    # 现在各尺寸已经提交在 resources/icons/<size>x<size>/apps/ 下，直接取用。
    icons_root = project_root / "resources" / "icons"
    # .icns 需要的十个条目由七个实际尺寸拼出来：@2x 与下一档同像素。
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
    iconutil = require_tool("iconutil")
    with tempfile.TemporaryDirectory(prefix="athena-icon-") as temporary:
        iconset = Path(temporary) / "Athena.iconset"
        iconset.mkdir()
        for filename, size in sizes.items():
            source = (
                icons_root / f"{size}x{size}" / "apps" / "cn.athena.icon.png"
            )
            if not source.is_file():
                raise PackagingError(
                    f"application icon not found: {source}. "
                    "图标尺寸集提交在 resources/icons/<size>x<size>/apps/ 下，"
                    "缺哪一档就补哪一档"
                )
            shutil.copy2(source, iconset / filename)
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
    macho_files = [app_path / "Contents" / "MacOS" / "athena-cpp"]
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
    nested.append(app_path / "Contents" / "MacOS" / "athena-cpp")
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
    parser.add_argument(
        "--version",
        help="optional; defaults to the meson.build version and must match it",
    )
    return parser


def main() -> int:
    if sys.platform != "darwin":
        raise PackagingError("macOS packaging must run on macOS")
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
    output_dir = args.output_dir.resolve()
    if not binary.is_file():
        raise PackagingError(f"Athena binary not found: {binary}")
    output_dir.mkdir(parents=True, exist_ok=True)

    architecture = architecture_name()
    app_path = output_dir / "Athena.app"
    dmg_path = output_dir / f"Athena-{version}-macos-{architecture}.dmg"
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

    executable = macos_dir / "athena-cpp"
    shutil.copy2(binary, executable)
    executable.chmod(0o755)
    render_templates(project_root, contents_dir, version)
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
