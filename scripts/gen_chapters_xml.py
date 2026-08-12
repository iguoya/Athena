#!/usr/bin/env python3
"""从 chapters.json 读取章节定义，生成 gresource.xml。

stdout: 每行 "chapter_id|blp_relative_path|ui_filename" 供 meson 解析。
不再扫描文件系统——所有元数据以 chapters.json 为单一来源。
"""
import json, os, sys


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: gen_chapters_xml.py <chapters.json> <project_root> <output_xml>",
            file=sys.stderr,
        )
        sys.exit(1)

    json_path = sys.argv[1]
    project_root = sys.argv[2]
    output_xml = sys.argv[3]

    with open(json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    chapters = config.get("chapters", [])
    if not chapters:
        print("Warning: no chapters defined in chapters.json", file=sys.stderr)

    # 校验 blp_file 存在，并去重（多个章节可能共用同一个 .blp 模板）
    seen_ui = {}       # ui_name -> blp_file（去重 .ui 条目）
    for ch in chapters:
        ch_id = ch.get("id", "")
        ui_resource = ch.get("ui_resource", f"/app/chapters/{ch_id}.ui")
        blp_file = ch.get("blp_file", "")

        if not blp_file:
            print(f"Warning: chapter '{ch_id}' has no blp_file, skipping", file=sys.stderr)
            continue

        blp_abs = os.path.join(project_root, blp_file)
        if not os.path.isfile(blp_abs):
            print(f"Error: blp_file not found for chapter '{ch_id}': {blp_abs}", file=sys.stderr)
            sys.exit(1)

        ui_name = os.path.basename(ui_resource)
        if ui_name not in seen_ui:
            seen_ui[ui_name] = blp_file

    ui_entries = []
    for ui_name in sorted(seen_ui):
        ui_entries.append(f'    <file compressed="true">{ui_name}</file>')

    # 写出 gresource.xml
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/app">
    <file preprocess="xml-stripblanks">window.ui</file>
  </gresource>
  <gresource prefix="/app/chapters">
{chr(10).join(ui_entries) if ui_entries else '    <!-- 暂无章节 -->'}
  </gresource>
  <gresource prefix="/app/data">
    <file compressed="true">chapters.json</file>
  </gresource>
  <gresource prefix="/app/icons">
    <file>icons/tiger.svg</file>
  </gresource>
</gresources>
"""
    os.makedirs(os.path.dirname(output_xml), exist_ok=True)
    with open(output_xml, "w", encoding="utf-8") as f:
        f.write(xml)

    # stdout 供 meson 解析: target_id|blp_relative_path|ui_filename（按 .ui 去重）
    for ui_name, blp_file in seen_ui.items():
        target_id = os.path.splitext(ui_name)[0]
        print(f"{target_id}|{blp_file}|{ui_name}")


if __name__ == "__main__":
    main()
