#!/usr/bin/env bash
# 把启动器装成 ~/Applications 下的常驻 .app：菜单栏图标、登录自启和全局
# 快捷键都需要一个正经的 bundle。仓库路径在这一步写进 Info.plist。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
APP_NAME="Athena Launcher.app"
STAGE="$ROOT/dist/$APP_NAME"
TARGET_DIR="${1:-$HOME/Applications}"

cd "$ROOT"
swift build -c release

rm -rf "$STAGE"
mkdir -p "$STAGE/Contents/MacOS" "$STAGE/Contents/Resources"
cp "$ROOT/.build/release/AthenaLauncher" "$STAGE/Contents/MacOS/AthenaLauncher"
sed "s|@ATHENA_ROOT@|$REPO|" "$ROOT/packaging/Info.plist" > "$STAGE/Contents/Info.plist"

# ad-hoc 签名：没有签名的 bundle 注册不了登录项，快捷键也会被系统怀疑。
codesign --force --sign - "$STAGE" >/dev/null

mkdir -p "$TARGET_DIR"
pkill -f "$APP_NAME/Contents/MacOS/AthenaLauncher" 2>/dev/null || true
rm -rf "$TARGET_DIR/$APP_NAME"
cp -R "$STAGE" "$TARGET_DIR/$APP_NAME"

echo "已安装：$TARGET_DIR/$APP_NAME（仓库指向 $REPO）"
open "$TARGET_DIR/$APP_NAME"
