#!/bin/bash
# macOS 双击入口：只转给跨平台的 restart_clean.py，不放任何逻辑。
exec python3 "$(dirname "$0")/restart_clean.py" "$@"
