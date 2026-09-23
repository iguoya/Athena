#!/usr/bin/env python3
"""把写课要用的公开教材拉到 content/sources/reference/。

Beej 允许私下镜像；c-faq 只供本机查阅，不进 git（见 .gitignore）。

原来是 fetch-sources.sh。内容生成也是日常环节，不该要求 Windows 上先装
Git Bash 或 curl（ADR 0047）；urllib 是标准库，三个平台都现成。

用法：
    python3 scripts/fetch-sources.py
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE = PROJECT_ROOT / "content" / "sources" / "reference"
USER_AGENT = "Mozilla/5.0 (compatible; AthenaC/0.1; personal offline reference)"

BEEJ_RAW = "https://raw.githubusercontent.com/beejjorgensen/bgc/main"
BEEJ_CHAPTERS = [
    "bgc_part_0400_pointers.md",
    "bgc_part_0500_arrays.md",
    "bgc_part_0600_strings.md",
    "bgc_part_0700_structs.md",
    "bgc_part_0800_pointers_2.md",
    "bgc_part_0850_malloc.md",
]
DIVE_PAGES = [
    "index",
    "pointers",
    "arrays",
    "scope_memory",
    "dynamic_memory",
    "strings",
    "structs",
]
CFAQ_SECTIONS = ["ptrs", "aryptr", "malloc"]


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def downloads() -> list[tuple[str, Path]]:
    """(URL, 落地路径) 的完整清单，声明在一处，好核对也好增删。"""
    items: list[tuple[str, Path]] = [
        (f"{BEEJ_RAW}/LICENSE.md", REFERENCE / "github/beej-bgc/LICENSE.md"),
        (f"{BEEJ_RAW}/README.md", REFERENCE / "github/beej-bgc/README.md"),
    ]
    items += [
        (f"{BEEJ_RAW}/src/{name}", REFERENCE / "github/beej-bgc/src" / name)
        for name in BEEJ_CHAPTERS
    ]
    items.append(
        (
            "https://diveintosystems.org/book/copyright.html",
            REFERENCE / "dive-into-systems/copyright.html",
        )
    )
    items += [
        (
            f"https://diveintosystems.org/book/C2-C_depth/{page}.html",
            REFERENCE / "dive-into-systems/C2-C_depth" / f"{page}.html",
        )
        for page in DIVE_PAGES
    ]
    # c-faq：作者禁止再发布，只落本机，已被 .gitignore。
    items += [
        (f"https://c-faq.com/{name}/index.html", REFERENCE / "c-faq" / f"{name}.html")
        for name in CFAQ_SECTIONS
    ]
    # C23 公开对照稿（正式 ISO 文本不抓）。PDF 已 gitignore。
    items.append(
        (
            "https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf",
            REFERENCE / "c23/n3220.pdf",
        )
    )
    return items


def fetch(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())
    print(f"  {destination.relative_to(REFERENCE)}", flush=True)


def main() -> int:
    _force_utf8_output()
    print(f"抓取到 {REFERENCE.relative_to(PROJECT_ROOT)}", flush=True)
    for url, destination in downloads():
        try:
            fetch(url, destination)
        except (urllib.error.URLError, OSError) as error:
            # 一条抓不下来就停：半套资料比没有资料更难发现问题。
            raise SystemExit(f"抓取失败 {url}：{error}") from error
    print("已更新。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
