#!/bin/sh
# Athena 统一验证入口：JSON 校验、生成器检查、构建与测试。
# 本地与 CI 共用，命令清单见 AGENTS.md「验证要求」。
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
build_dir=builddir
setup_extra=

usage() {
  echo "用法: scripts/check.sh [--build-dir DIR] [--buildtype TYPE]" >&2
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --build-dir)
      [ $# -ge 2 ] || usage
      build_dir=$2
      shift 2
      ;;
    --buildtype)
      [ $# -ge 2 ] || usage
      setup_extra="--buildtype=$2"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

cd "$project_root"

echo "== JSON 校验 =="
python3 -m json.tool resources/athena.json >/dev/null

echo "== 生成器检查 =="
python3 scripts/generate_project.py --project-root . --config resources/athena.json check

echo "== Meson 配置 =="
if [ -d "$build_dir" ]; then
  # shellcheck disable=SC2086
  meson setup "$build_dir" --reconfigure $setup_extra
else
  # shellcheck disable=SC2086
  meson setup "$build_dir" $setup_extra
fi

echo "== 构建 =="
meson compile -C "$build_dir"

echo "== 测试 =="
meson test -C "$build_dir" --print-errorlogs
