#!/usr/bin/env bash
# 把写课要用的公开教材拉到 content/sources/reference/。
# Beej 允许私下镜像；c-faq 只供本机查阅，不进 git。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)/content/sources/reference"
UA="Mozilla/5.0 (compatible; AthenaC/0.1; personal offline reference)"
mkdir -p "$ROOT/github/beej-bgc/src" "$ROOT/dive-into-systems/C2-C_depth" "$ROOT/c-faq" "$ROOT/modern-c" "$ROOT/c23"

curl -fsSL -A "$UA" -o "$ROOT/github/beej-bgc/LICENSE.md" \
  https://raw.githubusercontent.com/beejjorgensen/bgc/main/LICENSE.md
curl -fsSL -A "$UA" -o "$ROOT/github/beej-bgc/README.md" \
  https://raw.githubusercontent.com/beejjorgensen/bgc/main/README.md
for f in \
  bgc_part_0400_pointers.md \
  bgc_part_0500_arrays.md \
  bgc_part_0600_strings.md \
  bgc_part_0700_structs.md \
  bgc_part_0800_pointers_2.md \
  bgc_part_0850_malloc.md
do
  curl -fsSL -A "$UA" -o "$ROOT/github/beej-bgc/src/$f" \
    "https://raw.githubusercontent.com/beejjorgensen/bgc/main/src/$f"
done

curl -fsSL -A "$UA" -o "$ROOT/dive-into-systems/copyright.html" \
  https://diveintosystems.org/book/copyright.html
for page in index pointers arrays scope_memory dynamic_memory strings structs; do
  curl -fsSL -A "$UA" -o "$ROOT/dive-into-systems/C2-C_depth/${page}.html" \
    "https://diveintosystems.org/book/C2-C_depth/${page}.html"
done

# c-faq：作者禁止再发布，只落本机，已被 .gitignore。
curl -fsSL -A "$UA" -o "$ROOT/c-faq/ptrs.html" https://c-faq.com/ptrs/index.html
curl -fsSL -A "$UA" -o "$ROOT/c-faq/aryptr.html" https://c-faq.com/aryptr/index.html
curl -fsSL -A "$UA" -o "$ROOT/c-faq/malloc.html" https://c-faq.com/malloc/index.html

# C23 公开对照稿（正式 ISO 文本不抓）。PDF 已 gitignore。
curl -fsSL -A "$UA" -o "$ROOT/c23/n3220.pdf" \
  https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf

echo "已更新 $ROOT"
