project('Athena', 'cpp',
  version: '2.0.1',
  default_options: ['cpp_std=c++20'])

fs = import('fs')
gnome = import('gnome')

gtkmm_dep = dependency('gtkmm-4.0')
gtk4_dep = dependency('gtk4')
glib_dep = dependency('glib-2.0')
glibmm_dep = dependency('glibmm-2.68')
gio_dep = dependency('gio-2.0')
sourceview_dep = dependency('gtksourceview-5')
md4c_dep = dependency('md4c')
md4c_html_dep = dependency('md4c-html')
nlohmann_json_dep = dependency('nlohmann_json')
gtest_dep = dependency('gtest')
gtest_main_dep = dependency('gtest_main')
cc = meson.get_compiler('cpp')
sqlite3_dep = cc.find_library('sqlite3', has_headers: ['sqlite3.h'])
blueprint_compiler = find_program('blueprint-compiler')
python = find_program('python3')

article_view_sources = []
app_icon_sources = []
platform_dependencies = []
if host_machine.system() == 'darwin'
  add_languages('objcpp', native: false)
  article_view_sources += files('render/article_view_macos.mm')
  app_icon_sources += files('app_icon_macos.mm')
  platform_dependencies += [
    dependency('gtk4-macos'),
    dependency('appleframeworks', modules: ['AppKit', 'WebKit'])
  ]
elif host_machine.system() == 'linux'
  article_view_sources += files('render/article_view_webkitgtk.cc')
  app_icon_sources += files('app_icon_other.cc')
  platform_dependencies += dependency('webkitgtk-6.0')
else
  article_view_sources += files('render/article_view_unavailable.cc')
  app_icon_sources += files('app_icon_other.cc')
endif

# 业务逻辑类目录（C++ 语言各章节演示类）
language_inc = include_directories('language')

# 定义源码根目录，供运行时读取演示类源码（源码框显示）
add_project_arguments('-DATHENA_SOURCE_ROOT="' + meson.project_source_root() + '"', language: 'cpp')

# 版本号以 meson.build 为单一来源（见 AGENTS.md macOS 发行规则），关于对话框直接读取，
# 不在 C++ 里重复写死版本字符串。
add_project_arguments('-DATHENA_VERSION="' + meson.project_version() + '"', language: 'cpp')

# === 从 athena.json 读取项目定义（JSON 为单一数据源） ===
project_generator = meson.project_source_root() / 'scripts' / 'generate_project.py'
project_generator_sources = files(
  'scripts/generate_project.py',
  'scripts/project_generator/__init__.py',
  'scripts/project_generator/catalog.py',
  'scripts/project_generator/model.py',
  'scripts/project_generator/registry.py',
  'scripts/project_generator/resources.py',
  'scripts/project_generator/scaffold.py'
)
athena_json = meson.project_source_root() / 'resources' / 'athena.json'
gresource_xml = meson.current_build_dir() / 'app.gresource.xml'

# 脚本 stdout 格式: "chapter_id|blp_relative_path|ui_filename"
gen_output = run_command(
  python,
  project_generator,
  '--project-root', meson.project_source_root(),
  '--config', athena_json,
  'resources',
  '--output', gresource_xml,
  check: true
).stdout().strip().split('\n')

function_registry_generated = custom_target(
  'generate-function-registry',
  input: athena_json,
  depend_files: project_generator_sources,
  output: 'function_registry.generated.cc',
  command: [
    python,
    project_generator,
    '--project-root', meson.project_source_root(),
    '--config', '@INPUT@',
    'registry',
    '--output', '@OUTPUT@'
  ]
)

runtime_catalog_generated = custom_target(
  'generate-runtime-catalog',
  input: athena_json,
  depend_files: project_generator_sources,
  output: 'chapter_catalog.generated.json',
  command: [
    python,
    project_generator,
    '--project-root', meson.project_source_root(),
    '--config', '@INPUT@',
    'catalog',
    '--output', '@OUTPUT@'
  ]
)

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

# === 共享核心库 ===
core_sources = files(
  'content/content_loader.cc',
  'content/source_locator.cc',
  'practice/pocket_cube/state.cc',
  'registry/chapter_catalog.cc',
  'registry/function_registry.cc',
  'registry/progress_stats.cc',
  'render/chart_scale.cc',
  'render/markdown_renderer.cc',
  'services/ai_service.cc',
  'services/experiment_runner.cc',
  'storage/learning_store.cc'
) + [function_registry_generated]

athena_core_lib = static_library(
  'athena-core',
  core_sources,
  include_directories: [language_inc],
  dependencies: [glib_dep, glibmm_dep, gio_dep, md4c_dep, md4c_html_dep, nlohmann_json_dep, sqlite3_dep]
)

athena_core_dep = declare_dependency(
  link_with: athena_core_lib,
  include_directories: [language_inc],
  dependencies: [glib_dep, glibmm_dep, gio_dep, md4c_dep, md4c_html_dep, nlohmann_json_dep, sqlite3_dep]
)

# === 桌面应用源码 ===
app_sources = files(
  'main.cc',
  'athena.cc',
  'mainwindow.cc',
  'practice/pocket_cube/view.cc',
  'render/chart_view.cc',
  'ui/about_dialog.cc',
  'ui/ai_insight_dialog.cc',
  'ui/ai_markdown_dialog.cc',
  'ui/api_key_store.cc',
  'ui/chapter_nav_strip.cc',
  'ui/chapter_overview.cc',
  'ui/code_chapter_page.cc',
  'ui/dialog_helpers.cc',
  'ui/handbook_page.cc',
  'ui/history_dialog.cc',
  'ui/icon_utils.cc',
  'ui/learning_dialogs.cc',
  'ui/markdown_fallback.cc',
  'ui/pocket_cube_page.cc',
  'ui/progress_page.cc',
  'ui/quiz_dialog.cc',
  'ui/settings_dialog.cc',
  'ui/source_view.cc'
) + article_view_sources + app_icon_sources

# === 打包资源 ===
resources = gnome.compile_resources(
  'app-resources',
  gresource_xml,
  dependencies: compiled_ui + [runtime_catalog_generated],
  source_dir: ['resources', '.', meson.current_build_dir()]
)

executable('Athena', app_sources,
  sources: resources,
  include_directories: [language_inc],
  dependencies: [
    gtkmm_dep,
    gtk4_dep,
    glib_dep,
    sourceview_dep,
    athena_core_dep
  ] + platform_dependencies,
  install: true)

# === 桌面集成（Linux 任务栏图标与启动器条目；macOS 用 .app 内的 icns） ===
install_data(
  'resources/icons/scalable/apps/cn.athena.icon.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps'
)
install_data(
  'cn.yatiger.athena.desktop.in',
  rename: 'cn.athena.desktop',
  install_dir: get_option('datadir') / 'applications'
)

# === 测试 ===
# 核心测试不依赖 GTK，保证 JSON、Markdown 和注册表可独立验证。
core_test_exe = executable(
  'athena-core-tests',
  files(
    'tests/chapter_catalog_test.cc',
    'tests/ai_service_test.cc',
    'tests/content_loader_test.cc',
    'tests/experiment_runner_test.cc',
    'tests/function_registry_test.cc',
    'tests/learning_store_test.cc',
    'tests/chart_scale_test.cc',
    'tests/pocket_cube_state_test.cc',
    'tests/pocket_cube_test.cc',
    'tests/markdown_renderer_test.cc',
    'tests/progress_stats_test.cc',
    'tests/raii_content_test.cc',
    'tests/type_semantics_content_test.cc',
    'tests/source_locator_test.cc'
  ),
  sources: resources,
  include_directories: [language_inc],
  dependencies: [gtest_main_dep, athena_core_dep]
)
test('athena-core', core_test_exe)

# GTK 测试只检查 Blueprint/GResource 能否构造关键控件，不启动完整窗口。
gtk_test_exe = executable(
  'athena-gtk-tests',
  files(
    'tests/gtk_resource_test.cc',
    'tests/progress_page_test.cc',
    'tests/pocket_cube_view_test.cc',
    'practice/pocket_cube/view.cc',
    'render/chart_view.cc',
    'ui/progress_page.cc'
  ),
  sources: resources,
  include_directories: [language_inc],
  dependencies: [gtest_dep, gtkmm_dep, gtk4_dep, sourceview_dep, athena_core_dep]
)
test('athena-gtk-resources', gtk_test_exe, is_parallel: false)

# 配置校验不生成文件，保证 athena.json 的结构和所有路径引用有效。
test(
  'athena-project-check',
  python,
  args: [
    project_generator,
    '--project-root', meson.project_source_root(),
    '--config', athena_json,
    'check'
  ]
)

# 在临时目录端到端验证五个子命令，并检查 scaffold 不覆盖已有文件。
test(
  'athena-project-generator',
  python,
  args: [
    meson.project_source_root() / 'tests' / 'generate_project_test.py',
    project_generator
  ]
)
