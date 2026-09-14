#!/usr/bin/env python3
"""仓库统一验证入口（ADR 0007、0045、0047）。

检查逻辑归各应用自己（apps/<id>/scripts/check.py），这里只负责依次调用，
外加一项跨应用检查：内容必须有出处（ADR 0043）。新增应用放一份自己的
check.py 就会被带上，不用改这个文件，也不用改 CI。

用 Python 而不是 shell：验证每天都要跑，不该要求 Windows 上先装 Git Bash
或 WSL（ADR 0047）。

用法：
    python3 scripts/check.py                  跨应用检查 + 每个应用自己的检查
    python3 scripts/check.py cpp [参数...]    只跑某个应用，余下参数透传给它
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


def run_source_check() -> None:
    print("== 跨应用检查：内容必须有出处 ==", flush=True)
    node = shutil.which("node")
    if node is None:
        print("没有 node，跳过内容出处检查", file=sys.stderr)
        return
    completed = subprocess.run(
        [node, "scripts/check-app-sources.mjs"], cwd=REPO_ROOT
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main(argv: list[str]) -> int:
    _force_utf8_output()
    if argv:
        run_app(argv[0], argv[1:])
        return 0

    run_source_check()
    apps_root = REPO_ROOT / "apps"
    for entry in sorted(apps_root.iterdir()):
        if (entry / "scripts" / "check.py").is_file():
            run_app(entry.name, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
