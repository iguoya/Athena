#!/usr/bin/env python3
"""仓库统一验证入口（ADR 0007、0045、0047）。

检查逻辑归各应用自己（apps/<id>/scripts/check.py），这里只负责依次调用，
外加两项跨应用检查：内容必须有出处（ADR 0043），软件内容不出现具体院所名
（ADR 0055）。新增应用放一份自己的 check.py 就会被带上，不用改这个文件，
也不用改 CI。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash
或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py                  跨应用检查 + 每个应用自己的检查
    python3 scripts/check.py cpp [参数...]    只跑某个应用，余下参数透传给它
    python3 scripts/check.py --sources-only   只跑跨应用检查（出处 + 院所名）
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent



def _force_utf8_output() -> None:
    """Windows 控制台默认不是 UTF-8，打印中文会抛 UnicodeEncodeError。

    跨平台的做法是在入口处把标准流重设成 UTF-8，而不是把提示改成英文
    或者只在 CI 里设 PYTHONIOENCODING（ADR 0047）。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

def run_app(app: str, extra: list[str]) -> None:
    entry = REPO_ROOT / "apps" / app / "scripts" / "check.py"
    if not entry.is_file():
        raise SystemExit(f"应用 {app} 没有 {entry.relative_to(REPO_ROOT)}")
    print(f"== 检查应用：{app} ==", flush=True)
    completed = subprocess.run([sys.executable, str(entry), *extra], cwd=entry.parent.parent)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


# 不参与构建或不是人写的内容，扫了只会制造噪声。
_SKIP_DIRS = {
    ".git", "archive", "build", "builddir", "target", ".build",
    "node_modules", "dist", ".venv", "__pycache__",
}
_SKIP_SUFFIXES = {".db", ".png", ".jpg", ".jpeg", ".ico", ".icns", ".pdf", ".lock"}


def run_redaction_check() -> None:
    """软件内容里不许出现具体院所名，一律用「某所」（ADR 0055）。

    禁用词写成 Unicode 转义，不写字面量：这个文件自己会被扫到，写了字面量
    就等于给检查器留一个永久误报。
    """
    print("== 跨应用检查：软件内容不出现具体院所名 ==", flush=True)
    forbidden = "\u5341\u4e03\u6240"
    hits: list[tuple[Path, int, str]] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if forbidden not in text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if forbidden in line:
                hits.append((path.relative_to(REPO_ROOT), line_no, line.strip()[:120]))

    if hits:
        for rel, line_no, line in hits:
            print(f"  {rel}:{line_no}  {line}", flush=True)
        raise SystemExit(
            f"有 {len(hits)} 处写了具体所名。改成「某所」；"
            "确实要做禁用词检查的代码，把禁用词写成 Unicode 转义。"
        )


def run_source_check() -> None:
    print("== 跨应用检查：内容必须有出处 ==", flush=True)
    node = shutil.which("node")
    if node is None:
        # 不跳过。检查器自己的注释就写着「沉默地通过是最坏的结果」，入口更不该
        # 因为缺个 node 就把整项检查放过去还报通过。node 是开发必备工具，
        # 按仓库基线视为已装；没有就说清楚装什么（AGENTS.md「基线」一节）。
        raise SystemExit("没有 node，跨应用出处检查跑不了。装 Node.js 后重试。")
    completed = subprocess.run(
        [node, "scripts/check-app-sources.mjs"], cwd=REPO_ROOT
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main(argv: list[str]) -> int:
    _force_utf8_output()
    # CI 把跨应用检查和各应用检查拆成不同的 job 并行跑，需要单独触发前者；
    # 有了它，CI 的每一步都还是走这一个入口（ADR 0007）。
    if argv[:1] == ["--sources-only"]:
        run_redaction_check()
        run_source_check()
        return 0

    if argv:
        run_app(argv[0], argv[1:])
        return 0

    run_redaction_check()
    run_source_check()
    apps_root = REPO_ROOT / "apps"
    for entry in sorted(apps_root.iterdir()):
        if (entry / "scripts" / "check.py").is_file():
            run_app(entry.name, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
