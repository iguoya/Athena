#!/usr/bin/env bash
# 开发启动：对着源码跑 tauri:dev（热更新）。不要启动打包 .app / /Applications 里的副本。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="/usr/local/opt/node/bin:/opt/homebrew/bin:/usr/local/bin:$HOME/.cargo/bin:$PATH"
export ATHENA_ENGLISH_ROOT="$ROOT"
DEV_URL="http://localhost:1422"
APP_HINT="athena-english"

if command -v curl >/dev/null 2>&1 && curl -sf -o /dev/null --max-time 0.4 "$DEV_URL"; then
  echo "开发服务已在运行：$DEV_URL" >&2
  if [[ "$(uname -s)" == "Darwin" ]]; then
    osascript -e "tell application \"System Events\" to set frontmost of first process whose name contains \"${APP_HINT}\" to true" 2>/dev/null || true
  fi
  echo "请看已打开的「英语学习」窗口；不要再起一份，也不要打开 /Applications 里的旧包。" >&2
  exit 0
fi

cd "$ROOT"
if [[ ! -d node_modules ]]; then
  npm install
fi
exec npm run tauri:dev
