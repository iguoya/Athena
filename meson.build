project('Athena', 'cpp',
  version: '0.1',
  default_options: ['cpp_std=c++20'])

fs = import('fs')
gnome = import('gnome')

gtkmm_dep = dependency('gtkmm-4.0')
glib_dep = dependency('glib-2.0')
sourceview_dep = dependency('gtksourceview-5')
md4c_dep = dependency('md4c')
md4c_html_dep = dependency('md4c-html')
blueprint_compiler = find_program('blueprint-compiler')
python = find_program('python3')

article_view_sources = []
platform_dependencies = []
if host_machine.system() == 'darwin'
  add_languages('objcpp', native: false)
  article_view_sources += files('article_view_macos.mm')
  platform_dependencies += [
    dependency('gtk4-macos'),
    dependency('appleframeworks', modules: ['AppKit', 'WebKit'])
  ]
else
  article_view_sources += files('article_view_unavailable.cc')
endif

# 本地第三方头文件（nlohmann/json.hpp）
local_inc = include_directories('include')
# 业务逻辑类目录（C++ 语言各章节演示类）
language_inc = include_directories('language')

# 定义源码根目录，供运行时读取演示类源码（源码框显示）
add_project_arguments('-DATHENA_SOURCE_ROOT="' + meson.project_source_root() + '"', language: 'cpp')

# === 从 chapters.json 读取章节定义（JSON 为单一数据源） ===
gen_script = meson.project_source_root() / 'scripts' / 'gen_chapters_xml.py'
chapters_json = meson.project_source_root() / 'resources' / 'chapters.json'
gresource_xml = meson.project_source_root() / 'resources' / 'app.gresource.xml'

# 脚本 stdout 格式: "chapter_id|blp_relative_path|ui_filename"
gen_output = run_command(
  python, gen_script, chapters_json, meson.project_source_root(), gresource_xml,
  check: true
).stdout().strip().split('\n')

# === 编译所有 Blueprint 文件 ===
compiled_ui = []

foreach line : gen_output
  if line != ''
    # 解析 "id|blp_path|ui_filename"
    parts = line.split('|')
    ch_id = parts[0]
    blp_path = parts[1]
    ui_name = parts[2]
    compiled_ui += custom_target(
      'compile-' + ch_id,
      input: meson.project_source_root() / blp_path,
      output: ui_name,
      command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
    )
  endif
endforeach

# 主窗口 .blp（独立于章节目录）
compiled_ui += custom_target(
  'compile-window.blp',
  input: files('resources/ui/window.blp'),
  output: 'window.ui',
  command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
)

# === 源码 ===
src_files = files(
  'main.cc',
  'athena.cc',
  'mainwindow.cc',
  'chapter_catalog.cc',
  'demo_registry.cc',
  'markdown_renderer.cc',
  'language/raii/raii_basic.cpp',
  'language/raii/smart_pointer.cpp',
  'language/raii/move_semantics.cpp'
) + article_view_sources

# === 打包资源 ===
resources = gnome.compile_resources(
  'app-resources',
  gresource_xml,
  dependencies: compiled_ui,
  source_dir: ['resources', '.']
)

executable('Athena', src_files,
  sources: resources,
  include_directories: [local_inc, language_inc],
  dependencies: [
    gtkmm_dep,
    glib_dep,
    sourceview_dep,
    md4c_dep,
    md4c_html_dep
  ] + platform_dependencies,
  install: true)
