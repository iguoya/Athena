#!/usr/bin/env python3
"""把写课要用的公开教材拉到 content/sources/reference/。

Beej 允许私下镜像；c-faq 只供本机查阅，不进 git（见 .gitignore）。
汇编线（ADR 0005 第 9 条）的来源：DIS 汇编章、各 ABI 规范、GNU as 手册、Intel SDM。
Arm 的 ISA 文档（DDI 0602、DDI 0487）对脚本返回 403，只在 catalog 里登记网址。

原来是 fetch-sources.sh。内容生成也是日常环节，不该要求 Windows 上先装
Git Bash 或 curl（ADR 0047）；urllib 是标准库，三个平台都现成。

用法：
    python3 scripts/fetch-sources.py          # 全部
    python3 scripts/fetch-sources.py asm      # 只抓汇编线的来源（不碰已有的 C 教材副本）
    python3 scripts/fetch-sources.py c        # 只抓 C 教材
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

# DIS 汇编章：第 6 章导论、第 7 章 x86-64、第 9 章 ARMv8、第 10 章小结。
# 第 8 章 IA32（32 位）不在范围内。x86-64 章用 AT&T 语法；本应用不强制统一语法（ADR 0007），
# 引用时 locator 照原文的语法写即可。
DIS_ASM_SECTIONS = [
    "index", "basics", "common", "arithmetic", "conditional_control_loops",
    "preliminaries", "if_statements", "loops", "functions", "recursion",
    "arrays", "matrices", "structs", "buffer_overflow", "exercises",
]
DIS_ASM_CHAPTERS = {
    "C6-asm_intro": ["index"],
    "C7-x86_64": DIS_ASM_SECTIONS,
    "C9-ARM64": DIS_ASM_SECTIONS,
    "C10-asm_takeaways": ["index"],
}

# ABI 规范与手册。Microsoft 取 cpp-docs 的 Markdown 源文件（CC BY 4.0），比渲染后的网页干净。
MS_DOCS_RAW = "https://raw.githubusercontent.com/MicrosoftDocs/cpp-docs/main/docs/build"
MS_X64_PAGES = ["x64-calling-convention", "x64-software-conventions", "stack-usage"]
GNU_AS_BASE = "https://sourceware.org/binutils/docs/as"
# i386_002dSyntax 只是目录页，真正的内容在子页：Variations（AT&T 与 Intel 的差别）、Regs、Memory、
# Mnemonics（指令后缀）、Chars。
GNU_AS_PAGES = [
    "i386_002dSyntax", "i386_002dVariations", "i386_002dChars", "i386_002dRegs",
    "i386_002dMemory", "i386_002dMnemonics", "i386_002dDependent", "AArch64_002dDependent",
]
SYSV_ABI_PDF = (
    "https://gitlab.com/x86-psABIs/x86-64-ABI/-/jobs/artifacts/master/raw/x86-64-ABI/abi.pdf?job=build"
)
AAPCS64_RST = "https://raw.githubusercontent.com/ARM-software/abi-aa/main/aapcs64/aapcs64.rst"
# Intel 合订本的固定入口，会重定向到当前版本（抓取时是 325462-093）。26 MB，PDF 不进 git。
INTEL_SDM_PDF = "https://cdrdv2.intel.com/v1/dl/getContent/671200"
LARGE_TIMEOUT = 300


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
    items += [
        (
            f"https://diveintosystems.org/book/{chapter}/{page}.html",
            REFERENCE / "dive-into-systems" / chapter / f"{page}.html",
        )
        for chapter, pages in DIS_ASM_CHAPTERS.items()
        for page in pages
    ]
    items += [
        (f"{MS_DOCS_RAW}/{name}.md", REFERENCE / "ms-x64-abi" / f"{name}.md")
        for name in MS_X64_PAGES
    ]
    items += [
        (f"{GNU_AS_BASE}/{name}.html", REFERENCE / "gnu-as" / f"{name}.html")
        for name in GNU_AS_PAGES
    ]
    items += [
        (SYSV_ABI_PDF, REFERENCE / "sysv-abi/abi.pdf"),
        (AAPCS64_RST, REFERENCE / "aapcs64/aapcs64.rst"),
        (INTEL_SDM_PDF, REFERENCE / "intel-sdm/intel-sdm.pdf"),
    ]
    return items


def fetch(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    timeout = LARGE_TIMEOUT if destination.suffix == ".pdf" else 60
    with urllib.request.urlopen(request, timeout=timeout) as response:
        destination.write_bytes(response.read())
    print(f"  {destination.relative_to(REFERENCE)}", flush=True)


def is_asm(destination: Path) -> bool:
    """属于汇编线（ADR 0005 第 9 条）的来源。只抓一组时用它分开，免得改动已有的副本。"""
    top = destination.relative_to(REFERENCE).parts
    if top[0] in {"ms-x64-abi", "gnu-as", "sysv-abi", "aapcs64", "intel-sdm"}:
        return True
    return top[0] == "dive-into-systems" and len(top) > 1 and top[1] in DIS_ASM_CHAPTERS


def main() -> int:
    _force_utf8_output()
    group = sys.argv[1] if len(sys.argv) > 1 else "all"
    if group not in {"all", "asm", "c"}:
        raise SystemExit("用法：fetch-sources.py [all|asm|c]")
    print(f"抓取到 {REFERENCE.relative_to(PROJECT_ROOT)}（{group}）", flush=True)
    for url, destination in downloads():
        if group != "all" and is_asm(destination) != (group == "asm"):
            continue
        try:
            fetch(url, destination)
        except (urllib.error.URLError, OSError) as error:
            # 一条抓不下来就停：半套资料比没有资料更难发现问题。
            raise SystemExit(f"抓取失败 {url}：{error}") from error
    print("已更新。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
