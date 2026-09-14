#!/usr/bin/env bash
# 开发启动：编 C++ 壳（增量）并从源码树加载 QML。改教案保存即热加载。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="/usr/local/opt/qt@6/bin:/opt/homebrew/opt/qt@6/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
export ATHENA_C_ROOT="$ROOT"

for prefix in /usr/local/opt/qt@6 /opt/homebrew/opt/qt@6 /usr/local/opt/qt6 /opt/homebrew/opt/qt; do
  if [[ -d "$prefix/lib/cmake/Qt6" ]]; then
    export CMAKE_PREFIX_PATH="$prefix${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
    break
  fi
done

if pgrep -f "$ROOT/build/athena-c" >/dev/null 2>&1; then
  echo "C 语言教学应用已在运行。" >&2
  if [[ "$(uname -s)" == "Darwin" ]]; then
    osascript -e 'tell application "System Events" to set frontmost of first process whose name is "athena-c" to true' 2>/dev/null || true
  fi
  exit 0
fi

cd "$ROOT"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --target athena-c
exec "$ROOT/build/athena-c"
