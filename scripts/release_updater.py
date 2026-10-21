#!/usr/bin/env python3
"""应用内更新通道的 json 生成（ADR 0172）。

publish 作业把各应用的安装包和签名收在一个目录里（文件名由 release.yml 的「Collect and
rename artifacts」按约定产出），这里为每个出了更新工件的应用写一份 Tauri updater 读的
``<id>.json``（``latest.json`` 格式），之后由 publish 上传到固定标签 ``app-updates``。

文件名约定（版本是应用自己的版本，不是发版号，ADR 0171）：

- Windows：``athena-<app>-<版本>-windows-x64-setup.exe`` 与同名加 ``.sig``
- macOS：``athena-<app>-<版本>-macos-arm64.app.tar.gz`` / ``...-macos-x86_64.app.tar.gz``，各带 ``.sig``
- Linux 不出更新工件（ADR 0172 决策 5），通道里不写 Linux 条目。

只认带 ``.sig`` 的工件：签名密钥没配置时构建会跳过更新工件（release.yml 降级），那时这里
什么都不生成、退出码 0，通道保持上一版。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# 应用 id 里有连字符（selinger-linear-algebra），版本是纯数字三段，所以版本能把两边切开。
WINDOWS_SIG = re.compile(r"^athena-(?P<app>[a-z0-9][a-z0-9-]*)-(?P<ver>\d+\.\d+\.\d+)-windows-x64-setup\.exe\.sig$")
MACOS_SIG = re.compile(
    r"^athena-(?P<app>[a-z0-9][a-z0-9-]*)-(?P<ver>\d+\.\d+\.\d+)-macos-(?P<arch>arm64|x86_64)\.app\.tar\.gz\.sig$"
)
# Tauri updater 的平台键
MACOS_PLATFORM = {"arm64": "darwin-aarch64", "x86_64": "darwin-x86_64"}


def force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def collect(dist: Path) -> dict[str, dict]:
    """扫描 dist，按应用归拢：{app: {"version": x.y.z, "files": {平台键: 工件文件名}}}。"""
    apps: dict[str, dict] = {}
    for sig in sorted(dist.iterdir()):
        if not sig.is_file():
            continue
        win = WINDOWS_SIG.match(sig.name)
        mac = MACOS_SIG.match(sig.name)
        match = win or mac
        if match is None:
            continue
        platform = "windows-x86_64" if win else MACOS_PLATFORM[match.group("arch")]
        entry = apps.setdefault(match.group("app"), {"version": match.group("ver"), "files": {}})
        if entry["version"] != match.group("ver"):
            raise SystemExit(
                f"{match.group('app')} 的更新工件版本不一致：{entry['version']} 与 {match.group('ver')}（{sig.name}）"
            )
        entry["files"][platform] = sig.name[: -len(".sig")]
    return apps


def build_channel(app: str, entry: dict, dist: Path, tag: str, repo: str, notes: str, now: datetime) -> dict:
    platforms: dict[str, dict] = {}
    for platform, artifact in sorted(entry["files"].items()):
        # 签名文件的内容原样给 Tauri（minisign 文本的 base64），只去掉首尾空白
        signature = (dist / (artifact + ".sig")).read_text(encoding="utf-8").strip()
        if not signature:
            raise SystemExit(f"{artifact}.sig 是空的")
        platforms[platform] = {
            "signature": signature,
            "url": f"https://github.com/{repo}/releases/download/{tag}/{artifact}",
        }
    return {
        "version": entry["version"],
        "notes": notes,
        "pub_date": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platforms": platforms,
    }


def write_channels(dist: Path, tag: str, out: Path, repo: str, notes: str, now: datetime | None = None) -> list[Path]:
    now = now or datetime.now(timezone.utc)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for app, entry in sorted(collect(dist).items()):
        channel = build_channel(app, entry, dist, tag, repo, notes, now)
        target = out / f"{app}.json"
        target.write_text(json.dumps(channel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="应用内更新通道 json（ADR 0172）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    channels = sub.add_parser("channels", help="为 dist 里出了更新工件的每个应用写 <id>.json")
    channels.add_argument("--dist", type=Path, required=True)
    channels.add_argument("--tag", required=True, help="发版 tag，下载地址里的 releases/download/<tag>")
    channels.add_argument("--out", type=Path, required=True)
    channels.add_argument("--repo", required=True, help="owner/name")
    channels.add_argument("--notes-file", type=Path, help="更新说明，缺省为空串")
    args = parser.parse_args(argv)
    notes = args.notes_file.read_text(encoding="utf-8").strip() if args.notes_file and args.notes_file.is_file() else ""
    written = write_channels(args.dist, args.tag, args.out, args.repo, notes)
    for path in written:
        print(f"{path.name}")
    if not written:
        print("没有带签名的更新工件，通道保持原样")
    return 0


if __name__ == "__main__":
    sys.exit(main())
