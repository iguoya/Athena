#!/usr/bin/env sh
# 建符号引擎的 Python 环境（ADR 0025 第 2 节）。
# 显式运行，不挂进构建——沿用主仓库「scaffold 只能显式运行」的取向。
set -e
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
VENV=engine/.venv

if [ ! -x "$VENV/bin/python" ]; then
  echo "创建 $VENV（用 $PY）"
  # 用 venv 不是洁癖：Python 3.12 起的 PEP 668 会直接拒绝往系统环境装包
  "$PY" -m venv "$VENV"
fi

echo "安装 sympy"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet sympy

"$VENV/bin/python" - <<'PY'
import time
t = time.perf_counter()
import sympy
print(f"sympy {sympy.__version__} 就绪，import 耗时 {(time.perf_counter()-t)*1000:.0f} ms")
PY
echo "好了。验算功能现在可用。"
