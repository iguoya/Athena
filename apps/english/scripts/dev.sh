#!/usr/bin/env bash
# 开发启动：补齐常见 PATH 后跑 Tauri（不必先开 Athena）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="/usr/local/opt/node/bin:/opt/homebrew/bin:/usr/local/bin:$HOME/.cargo/bin:$PATH"
cd "$ROOT"
if [[ ! -d node_modules ]]; then
  npm install
fi
exec npm run tauri:dev
