#!/usr/bin/env python3
"""启用仓库自带的 Git 钩子（ADR 0170）：把 core.hooksPath 指到 scripts/hooks。

只改本仓库的本地配置，不碰全局。克隆后跑一次：python3 scripts/install_hooks.py
撤销：git config --unset core.hooksPath
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    subprocess.run(["git", "config", "core.hooksPath", "scripts/hooks"], cwd=REPO_ROOT, check=True)
    print("已启用 scripts/hooks（pre-push 会先跑 check.py --sources-only）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
