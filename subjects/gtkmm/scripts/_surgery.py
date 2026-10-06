#!/usr/bin/env python3
"""手术脚本：extract_source.py 改为从 inline_md.py 导入，删除旧损坏实现。"""
from pathlib import Path

BS = chr(92)
p = Path("scripts/extract_source.py")
lines = p.read_text(encoding="utf-8").splitlines()

# 定位旧 inline_md 与 strip_inline_md 的行区间（含注释块）
start_inline = next(i for i, l in enumerate(lines) if l.startswith("def inline_md"))
# inline_md 前面的注释块起点（"# 内联格式序列化"）
while start_inline > 0 and lines[start_inline - 1].startswith("#"):
    start_inline -= 1
end_strip = next(i for i, l in enumerate(lines) if l.startswith("def strip_inline_md"))
while not lines[end_strip].startswith("def ") and end_strip < len(lines):
    end_strip += 1
# strip_inline_md 函数体到下一个顶层定义/文件尾
end = end_strip + 1
while end < len(lines) and not (lines[end].startswith("def ") or lines[end].startswith("class ")):
    end += 1

# 找 expand_entities 旧定义（如果在本文件）也一并删除
expand_start = next(
    (i for i, l in enumerate(lines) if l.startswith("def expand_entities")), None)
if expand_start is not None:
    expand_end = expand_start + 1
    while expand_end < len(lines) and not (
        lines[expand_end].startswith("def ") or lines[expand_end].startswith("class ")
    ):
        expand_end += 1
else:
    expand_start, expand_end = None, None

# 删除区间（从后往前）
ranges = sorted(
    [r for r in [(start_inline, end), (expand_start, expand_end)] if r[0] is not None],
    reverse=True,
)
for a, b in ranges:
    del lines[a:b]

# 导入替换
for i, l in enumerate(lines):
    if l.startswith("from inline_md import") or l.startswith("from extract_source import"):
        continue
# 在 sys.path 注入行之后插入导入
path_import = next(i for i, l in enumerate(lines) if l.startswith("from pathlib import Path"))
lines.insert(path_import + 1, "from inline_md import expand_entities, inline_md, strip_inline_md  # noqa: E402")

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("手术完成；剩余 inline_md 引用检查：")
for i, l in enumerate(lines):
    if "strip_inline_md" in l and "import" not in l:
        print("  使用点:", i, l.strip()[:70])
print("expand_entities 残留定义:", any(l.startswith("def expand_entities") for l in lines))
