#!/usr/bin/env python3
"""按 third_party.lock.json 取回 c-gui-lab 构建所需的 third_party 子集。

- 校验每项 zip 的 sha256，不符则报错退出
- 只解出锁文件列出的构建子集（imgui / lvgl 不全量落盘）
- 先清空目标再写入，再打补丁，重复运行不叠补丁
- Windows 上为 lvgl/lvgl.h 建 junction；其他平台用 symlink
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "third_party.lock.json"
THIRD_PARTY = ROOT / "third_party"


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    print(f"download {url}")
    try:
        with urllib.request.urlopen(url) as resp, tmp.open("wb") as out:
            shutil.copyfileobj(resp, out)
        tmp.replace(dest)
    except Exception as exc:  # noqa: BLE001 — 网络错误要落成可读信息
        if tmp.exists():
            tmp.unlink()
        die(f"download failed: {url}: {exc}")


def ensure_archive(pkg: dict, cache: Path) -> Path:
    url = pkg["url"]
    digest = pkg["sha256"].lower()
    name = f"{pkg['id']}-{pkg['version'].replace('/', '_')}.zip"
    # 版本串可能很长；用 id + sha 前缀更稳
    name = f"{pkg['id']}-{digest[:16]}.zip"
    path = cache / name
    if path.exists():
        got = sha256_file(path)
        if got.lower() == digest:
            print(f"cache hit {path.name}")
            return path
        print(f"cache stale {path.name} (got {got}, want {digest}); re-download")
        path.unlink()
    download(url, path)
    got = sha256_file(path)
    if got.lower() != digest:
        path.unlink(missing_ok=True)
        die(f"sha256 mismatch for {pkg['id']}: got {got}, want {digest}")
    print(f"sha256 ok {pkg['id']}")
    return path


def rm_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    # Windows junction：is_dir() 为 True，用 rmdir / junction 删除
    if os.name == "nt":
        try:
            if path.is_junction():  # py3.12+
                path.rmdir()
                return
        except AttributeError:
            pass
    shutil.rmtree(path)


def extract_member(zf: zipfile.ZipFile, member: str, dest_file: Path) -> None:
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(member) as src, dest_file.open("wb") as out:
        shutil.copyfileobj(src, out)


def install_package(pkg: dict, archive: Path, dest_root: Path) -> None:
    strip = pkg["strip_prefix"].rstrip("/") + "/"
    dest_rel = pkg.get("dest", ".")
    package_dest = dest_root if dest_rel in (".", "") else dest_root / dest_rel

    # 幂等：清掉本包会写到的目标
    wipe: set[Path] = set()
    if "files" in pkg and dest_rel not in (".", ""):
        wipe.add(package_dest)
    if "trees" in pkg and dest_rel not in (".", ""):
        wipe.add(package_dest)
    for item in pkg.get("map", []):
        wipe.add(dest_root / item["to"])
    for g in pkg.get("glob_map", []):
        # style_*.h 落到 third_party 根；清已知 pattern 由写出覆盖，这里只清 map 目标
        pass
    if "alias" in pkg:
        for link_name in pkg["alias"]:
            wipe.add(dest_root / link_name)

    for p in sorted(wipe, key=lambda x: len(str(x)), reverse=True):
        rm_path(p)

    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()

        def full(rel: str) -> str:
            return strip + rel.replace("\\", "/")

        for rel in pkg.get("files", []):
            member = full(rel)
            if member not in names and member + "/" not in names:
                # zip 里可能是正斜杠
                alts = [n for n in names if n.replace("\\", "/") == member]
                if not alts:
                    die(f"{pkg['id']}: missing {member} in archive")
                member = alts[0]
            extract_member(zf, member, package_dest / rel)

        for tree in pkg.get("trees", []):
            prefix = full(tree.rstrip("/") + "/")
            matched = [n for n in names if n.replace("\\", "/").startswith(prefix) and not n.endswith("/")]
            if not matched:
                die(f"{pkg['id']}: empty tree {tree}")
            for member in matched:
                rel = member.replace("\\", "/")[len(strip) :]
                extract_member(zf, member, package_dest / rel)

        for item in pkg.get("map", []):
            member = full(item["from"])
            if member not in names:
                alts = [n for n in names if n.replace("\\", "/") == member]
                if not alts:
                    die(f"{pkg['id']}: missing map source {member}")
                member = alts[0]
            extract_member(zf, member, dest_root / item["to"])

        for g in pkg.get("glob_map", []):
            import fnmatch

            pattern = full(g["from_glob"])
            to_dir = dest_root / g.get("to_dir", ".")
            # 清掉将要写出的同名文件，避免残留
            for old in to_dir.glob(Path(g["from_glob"]).name):
                if old.is_file():
                    old.unlink()
            hit = 0
            for member in names:
                norm = member.replace("\\", "/")
                if norm.endswith("/"):
                    continue
                if fnmatch.fnmatch(norm, pattern):
                    extract_member(zf, member, to_dir / Path(norm).name)
                    hit += 1
            if hit == 0:
                die(f"{pkg['id']}: glob matched nothing: {g['from_glob']}")

    if "alias" in pkg:
        for link_name, target_name in pkg["alias"].items():
            make_alias(dest_root / link_name, dest_root / target_name)


def make_alias(link: Path, target: Path) -> None:
    rm_path(link)
    if not target.exists():
        die(f"alias target missing: {target}")
    if os.name == "nt":
        # junction 不要求管理员；指向绝对路径更稳
        import subprocess

        abs_target = str(target.resolve())
        abs_link = str(link)
        # mklink /J 是 cmd 内建
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", abs_link, abs_target],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            die(f"junction failed: {completed.stderr or completed.stdout}")
        print(f"junction {link.name} -> {target.name}")
    else:
        link.symlink_to(target.name, target_is_directory=True)
        print(f"symlink {link.name} -> {target.name}")


def apply_patches(patch_paths: list[str], dest_root: Path) -> None:
    """用 git apply；先 --check 再打，失败即退出。目标已是干净上游，故不会叠补丁。"""
    import subprocess

    for rel in patch_paths:
        patch = ROOT / rel
        if not patch.is_file():
            die(f"patch missing: {patch}")
        # 在 third_party 根上 -p1（补丁路径形如 a/microui/...）
        check = subprocess.run(
            ["git", "apply", "--check", "-p1", str(patch)],
            cwd=dest_root,
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            die(f"patch does not apply cleanly: {rel}\n{check.stderr}")
        applied = subprocess.run(
            ["git", "apply", "-p1", str(patch)],
            cwd=dest_root,
            capture_output=True,
            text=True,
        )
        if applied.returncode != 0:
            die(f"patch apply failed: {rel}\n{applied.stderr}")
        print(f"patched {rel}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache",
        type=Path,
        default=THIRD_PARTY / ".cache",
        help="下载缓存目录（默认 third_party/.cache）",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=THIRD_PARTY,
        help="解压目标（默认 third_party/）",
    )
    args = parser.parse_args()

    if not LOCK_PATH.is_file():
        die(f"lock file not found: {LOCK_PATH}")

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    dest_root: Path = args.dest
    dest_root.mkdir(parents=True, exist_ok=True)
    cache: Path = args.cache
    cache.mkdir(parents=True, exist_ok=True)

    for pkg in lock["packages"]:
        print(f"=== {pkg['id']} ({pkg['version']}) ===")
        archive = ensure_archive(pkg, cache)
        install_package(pkg, archive, dest_root)

    print("=== patches ===")
    apply_patches(lock.get("patches", []), dest_root)
    print("done.")


if __name__ == "__main__":
    main()
