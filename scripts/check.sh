#!/bin/sh
# 仓库统一验证入口（ADR 0007、0045）。
#
# 检查逻辑归各应用自己（apps/<id>/scripts/check.sh），这里只负责依次调用，
# 外加一项跨应用检查：内容必须有出处（ADR 0043）。新增应用放一份自己的
# check.sh 就会被带上，不用改这个文件，也不用改 CI。
#
# 用法：
#   scripts/check.sh                  跑跨应用检查 + 每个应用自己的检查
#   scripts/check.sh cpp [参数...]    只跑某个应用，余下参数原样透传给它

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
cd "$repo_root"

run_app() {
  app=$1
  shift
  entry="apps/$app/scripts/check.sh"
  if [ ! -x "$entry" ]; then
    echo "应用 $app 没有可执行的 $entry" >&2
    return 1
  fi
  echo "== 检查应用：$app =="
  "$entry" "$@"
}

if [ $# -gt 0 ]; then
  app=$1
  shift
  run_app "$app" "$@"
  exit 0
fi

echo "== 跨应用检查：内容必须有出处 =="
if command -v node >/dev/null 2>&1; then
  node scripts/check-app-sources.mjs
else
  echo "没有 node，跳过内容出处检查" >&2
fi

for entry in apps/*/scripts/check.sh; do
  [ -x "$entry" ] || continue
  app=$(basename "$(dirname "$(dirname "$entry")")")
  run_app "$app"
done
