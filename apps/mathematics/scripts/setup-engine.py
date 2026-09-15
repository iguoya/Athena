#!/usr/bin/env python3
"""建符号引擎的 Python 环境（ADR 0025 第 2 节）。

显式运行，不挂进构建——沿用「scaffold 只能显式运行」的取向。

原来是 setup-engine.sh。验证、生成、启动这些每天都跑的环节不允许依赖
`.sh`，否则 Windows 要先装 Git Bash 或 WSL（ADR 0047）。venv 在 POSIX 上
是 bin/python、在 Windows 上是 Scripts/python.exe，这里不自己判断，让标准库
的 EnvBuilder 把布局差异吃掉。

用法：
    python3 scripts/setup-engine.py
"""

from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / "engine" / ".venv"


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def ensure_venv() -> Path:
    """建出环境并返回它自己的解释器路径。

    用 venv 不是洁癖：Python 3.12 起的 PEP 668 会直接拒绝往系统环境装包。
    """
    builder = venv.EnvBuilder(with_pip=True)
    context = builder.ensure_directories(VENV_DIR)
    interpreter = Path(context.env_exe)
    if not interpreter.exists():
        print(f"创建 {VENV_DIR.relative_to(PROJECT_ROOT)}（用 {sys.executable}）", flush=True)
        builder.create(VENV_DIR)
    return interpreter


def run(command: list[str], step: str) -> None:
    print(step, flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    _force_utf8_output()
    interpreter = ensure_venv()
    # 走 `python -m pip` 而不是 venv 里的 pip 可执行文件：后者在 Windows 上
    # 叫 pip.exe，且被移动过的环境里那个壳会失效。
    run([str(interpreter), "-m", "pip", "install", "--quiet", "--upgrade", "pip"], "升级 pip")
    run([str(interpreter), "-m", "pip", "install", "--quiet", "sympy"], "安装 sympy")
    run(
        [
            str(interpreter),
            "-c",
            "import time;t=time.perf_counter();import sympy;"
            "print(f'sympy {sympy.__version__} 就绪，import 耗时 "
            "{(time.perf_counter()-t)*1000:.0f} ms')",
        ],
        "自检",
    )
    print("好了。验算功能现在可用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
