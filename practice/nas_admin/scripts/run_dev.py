#!/usr/bin/env python3
"""本机开发自举：venv 路径的平台差异关在这里。

用法（app.json 的 dev 块只认这两个子命令）：
    python3 scripts/run_dev.py bootstrap   # 建 .venv 并安装 requirements.txt
    python3 scripts/run_dev.py serve       # 用 .venv 里的 Python 跑 app.py

路由器上不用这个脚本：那边由 procd 直接 `/usr/bin/python3 /opt/webapp/app.py`，
依赖装在系统 Python 里（见 scripts/deploy.py）。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = APP_ROOT / ".venv"


def venv_python() -> Path:
    # Windows: .venv/Scripts/python.exe；macOS/Linux: .venv/bin/python
    candidate = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not candidate.is_file():
        raise SystemExit("虚拟环境不存在，先跑 scripts/run_dev.py bootstrap")
    return candidate


def bootstrap() -> int:
    print(f"[准备] 创建虚拟环境 {VENV_DIR}", flush=True)
    completed = subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], cwd=APP_ROOT)
    if completed.returncode != 0:
        return completed.returncode
    print("[准备] 安装 requirements.txt", flush=True)
    return subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=APP_ROOT,
    ).returncode


def serve() -> int:
    print("[启动] nas-admin（Flask-AppBuilder，http://127.0.0.1:5000）", flush=True)
    return subprocess.call([str(venv_python()), "app.py"], cwd=APP_ROOT)


def main(argv: list[str]) -> int:
    if argv == ["bootstrap"]:
        return bootstrap()
    if argv == ["serve"]:
        if not VENV_DIR.is_dir():
            code = bootstrap()
            if code != 0:
                return code
        return serve()
    raise SystemExit(f"不认识的参数：{argv}（可用：bootstrap / serve）")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
