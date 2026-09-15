#!/usr/bin/env bash
# 把启动器装成 ~/Applications 下的常驻 .app：菜单栏图标、登录自启和全局
# 快捷键都需要一个正经的 bundle。仓库路径在这一步写进 Info.plist。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/../.." && pwd)"
APP_NAME="Athena Launcher.app"
TARGET_DIR="${1:-$HOME/Applications}"

# 组装目录放在仓库外并随退出删掉：留在 dist/ 下的那份会被 Spotlight 和
# LaunchServices 当成第二个「Athena Launcher」索引，于是搜出来两个同名应用，
# 还可能从中间产物那份启动。
STAGE_ROOT="$(mktemp -d)"
trap 'rm -rf "$STAGE_ROOT"' EXIT
STAGE="$STAGE_ROOT/$APP_NAME"

cd "$ROOT"
swift build -c release

mkdir -p "$STAGE/Contents/MacOS" "$STAGE/Contents/Resources"
cp "$ROOT/.build/release/AthenaLauncher" "$STAGE/Contents/MacOS/AthenaLauncher"
sed "s|@ATHENA_ROOT@|$REPO|" "$ROOT/packaging/Info.plist" > "$STAGE/Contents/Info.plist"

# ad-hoc 签名：没有签名的 bundle 注册不了登录项，快捷键也会被系统怀疑。
codesign --force --sign - "$STAGE" >/dev/null

mkdir -p "$TARGET_DIR"
# 按进程名收，不按路径收：直接跑 .build/ 里那个裸二进制的实例（调试时很容易
# 留下，甚至会被注册成登录项）不在 bundle 路径下，按路径匹配抓不到它。
pkill -x AthenaLauncher 2>/dev/null || true
rm -rf "$TARGET_DIR/$APP_NAME"
cp -R "$STAGE" "$TARGET_DIR/$APP_NAME"

echo "已安装：${TARGET_DIR}/${APP_NAME}（仓库指向 ${REPO}）"
open "${TARGET_DIR}/${APP_NAME}"
