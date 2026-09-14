#!/bin/sh
# 开发时启动 Athena：增量编译 -> 清掉上一次的实例 -> 前台运行。
#
# 为什么用它而不是 VS Code 调试模式启动：
#  - 前台运行，Ctrl+C 一下就干净退出，不经过调试器的 ptrace，
#    不会留下 STAT=X、连 kill -9 都杀不掉的僵尸进程；
#  - 终端里直接看到程序往 stderr 打的日志（cerr 那些错误信息）；
#  - 改完代码重跑：Ctrl+C 停掉，再执行一次本脚本即可。
# 只有需要断点单步时才用 VS Code 的「Athena（macOS：构建并用 LLDB 调试）」
# 配置（CodeLLDB），且每次重开前先 Shift+F5 停干净。
#
# 用法：scripts/dev-run.sh [--build-dir DIR]

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
build_dir=builddir

while [ $# -gt 0 ]; do
  case "$1" in
    --build-dir)
      [ $# -ge 2 ] || { echo "用法: scripts/dev-run.sh [--build-dir DIR]" >&2; exit 2; }
      build_dir=$2
      shift 2
      ;;
    *)
      echo "未知参数: $1" >&2
      exit 2
      ;;
  esac
done

cd "$project_root"

if [ ! -d "$build_dir" ]; then
  echo "== 构建目录 $build_dir 不存在，先 meson setup =="
  meson setup "$build_dir" --buildtype=debug
fi

echo "== 增量编译 =="
meson compile -C "$build_dir"

# 清掉上一次残留：调试器留下的 debugserver（会挂住被 trace 的进程），
# 以及还在跑的 Athena 本身。找不到就跳过。
pkill -f "vscode-lldb.*debugserver" 2>/dev/null || true
pkill -f "$project_root/$build_dir/Athena" 2>/dev/null || true

# 用绝对路径 exec：进程的命令行里带着完整路径，上面那条 pkill、以及
# 菜单栏启动器的状态探测才认得出这是哪一份 Athena。
echo "== 启动 Athena（Ctrl+C 退出）=="
exec "$project_root/$build_dir/Athena"
