#!/usr/bin/env bash
# 开发启动：增量编译并直接跑源码产物，改完即时看到。
# 日常常驻请用 install.sh 装出来的 .app（能登录自启、能被系统当成正经应用）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

swift build

# 同一时刻只该有一个启动器：菜单栏上出现两个图标比慢更烦人。
pkill -f "$ROOT/.build/.*/AthenaLauncher" 2>/dev/null || true
pkill -f "Athena Launcher.app/Contents/MacOS/AthenaLauncher" 2>/dev/null || true

export ATHENA_ROOT="$(cd "$ROOT/../.." && pwd)"
exec "$ROOT/.build/debug/AthenaLauncher"
