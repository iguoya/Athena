project('Athena', 'cpp',
  version: '6.0.0',
  default_options: ['cpp_std=c++20'])

fs = import('fs')
gnome = import('gnome')

gtkmm_dep = dependency('gtkmm-4.0')
gtk4_dep = dependency('gtk4')
glib_dep = dependency('glib-2.0')
glibmm_dep = dependency('glibmm-2.68')
gio_dep = dependency('gio-2.0')
# giomm：GResource 与子进程的 C++ 绑定，骨架案例要用（ADR 0053）。属于 glibmm
# 同族、不是 GTK，所以 athena-core 用它不破坏 ADR 0004 的「与 GTK 解耦」。
giomm_dep = dependency('giomm-2.68')

# C 库与它的 C++ 绑定必须**配套**，不能各走各的版本。
#
# glib 2.89.2 起把 GEmblem / GDBusActionGroup / GdkCursor 等改用
# G_DECLARE_FINAL_TYPE 声明，该宏生成的是匿名结构体的 typedef；glibmm 2.89.0
# 随即改了包装方式（发行说明：“Don't derive gtkmm__Gxxx types. The underlying
# C classes are final types since GLib 2.89.2.”）。两边版本错配时，编译器吐的是
# 一串 `conflicting declaration ... GDBusActionGroupClass`，看不出跟版本有关，
# 排查成本很高——2026-09-15 就因此绕了一大圈（主仓库 ADR 0049）。
#
# 所以在配置期直接把话说清楚。这不是给某个平台开的特例：三个平台同一条规则，
# 谁先撞上谁先报。
if glib_dep.version().version_compare('>= 2.89.2') and glibmm_dep.version().version_compare('< 2.89.0')
  # 不报错停下——目标是能跑，不是依赖形式上配套。用垫片把名字冲突绕开，
  # 并说清楚现状，免得后来的人对着一串 conflicting declaration 猜半天。
  message(
    'glib @0@ 比 glibmm @1@ 新了一代（final type 改动），启用 compat/glib_final_type_shim.h 绕开名字冲突。MSYS2 更新 glibmm 到 2.89+ 后即可删除该垫片。'.format(
      glib_dep.version(), glibmm_dep.version()))
  add_project_arguments(
    '-include', meson.project_source_root() / 'compat' / 'glib_final_type_shim.h',
    language: 'cpp')
endif
sourceview_dep = dependency('gtksourceview-5')
md4c_dep = dependency('md4c')
nlohmann_json_dep = dependency('nlohmann_json')
gtest_dep = dependency('gtest')
gtest_main_dep = dependency('gtest_main')
cc = meson.get_compiler('cpp')
sqlite3_dep = cc.find_library('sqlite3', has_headers: ['sqlite3.h'])
blueprint_compiler = find_program('blueprint-compiler')
# .blp 里有中文，而 blueprint-compiler 打开文件时不指定编码，Windows 上会按
# 系统代码页解码然后崩掉。PYTHONUTF8=1 让 Python 全程按 UTF-8 读写（ADR 0047：
# 跨平台在构建规则里解决，不靠使用者自己设环境变量）。
blueprint_env = environment()
blueprint_env.set('PYTHONUTF8', '1')
python = find_program('python3')

# 平台专用源文件已经清空（ADR 0047）：菜单栏按 GTK 设置项判断，
# 应用图标交给 .app 的 Info.plist 和图标主题，URI 交给系统默认处理器。
# 这里只保留 macOS 构建真正需要的依赖。
platform_dependencies = []
if host_machine.system() == 'darwin'
  platform_dependencies += [dependency('gtk4-macos')]
endif

# 业务逻辑类目录（C++ 语言各章节演示类）
cplusplus_inc = include_directories('cplusplus')

# 定义源码根目录，供运行时读取演示类源码（源码框显示）
# 测试要按路径读源码树里的原始文件（生成器产物、athena.json），需要知道源码根。
# 只给测试目标，不进生产代码：编译期绝对路径装到别的机器就失效（ADR 0047）。
test_source_root_arg = '-DATHENA_SOURCE_ROOT="' + meson.project_source_root() + '"'

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
      env: blueprint_env,
    )
  endif
endforeach

# 主窗口 .blp（独立于章节目录）
compiled_ui += custom_target(
  'compile-window.blp',
  input: files('resources/ui/window.blp'),
  output: 'window.ui',
  command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
  env: blueprint_env,
)

compiled_ui += custom_target(
  'compile-learning_unit.blp',
  input: files('resources/ui/learning_unit.blp'),
  output: 'learning_unit.ui',
  command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
  env: blueprint_env,
)

compiled_ui += custom_target(
  'compile-checkpoint.blp',
  input: files('resources/ui/checkpoint.blp'),
  output: 'checkpoint.ui',
  command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
  env: blueprint_env,
)

compiled_ui += custom_target(
  'compile-lesson_blocks.blp',
  input: files('resources/ui/lesson_blocks.blp'),
  output: 'lesson_blocks.ui',
  command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
  env: blueprint_env,
)

compiled_ui += custom_target(
  'compile-outline.blp',
  input: files('resources/ui/outline.blp'),
  output: 'outline.ui',
  command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
  env: blueprint_env,
)

# === 共享核心库 ===
core_sources = files(
  'content/content_loader.cc',
  'content/doc_model.cc',
  'content/source_locator.cc',
  'platform/app_paths.cc',
  'practice/pocket_cube/state.cc',
  'registry/chapter_catalog.cc',
  'registry/domain_graph.cc',
  'registry/function_registry.cc',
  'registry/knowledge_graph.cc',
  'registry/progress_stats.cc',
  'render/chart_scale.cc',
  'services/ai_service.cc',
  'services/case_runner.cc',
  'services/case_workspace.cc',
  'services/experiment_runner.cc',
  'storage/learning_store.cc'
) + [function_registry_generated]

athena_core_lib = static_library(
  'athena-core',
  core_sources,
  include_directories: [cplusplus_inc],
  dependencies: [glib_dep, glibmm_dep, gio_dep, giomm_dep, md4c_dep, nlohmann_json_dep, sqlite3_dep]
)

athena_core_dep = declare_dependency(
  link_with: athena_core_lib,
  include_directories: [cplusplus_inc],
  dependencies: [glib_dep, glibmm_dep, gio_dep, giomm_dep, md4c_dep, nlohmann_json_dep, sqlite3_dep]
)

# === 桌面应用源码 ===
app_sources = files(
  'main.cc',
  'ui/athena.cc',
  'ui/mainwindow.cc',
  'platform/menu_bar_platform.cc',
  'practice/pocket_cube/view.cc',
  'render/cairo_shapes.cc',
  'render/cairo_text.cc',
  'render/chart_view.cc',
  'render/document_view.cc',
  'render/lesson_figure.cc',
  'render/domain_graph_view.cc',
  'render/knowledge_graph_view.cc',
  'render/roadmap_view.cc',
  'ui/about_dialog.cc',
  'ui/ai_insight_dialog.cc',
  'ui/ai_markdown_dialog.cc',
  'ui/api_key_store.cc',
  'ui/chapter_index_page.cc',
  'ui/chapter_overview.cc',
  'ui/chapter_page_stack.cc',
  'ui/code_chapter_page.cc',
  'ui/dialog_helpers.cc',
  'ui/experiment_dock.cc',
  'ui/experiment_page.cc',
  'ui/external_app_launcher.cc',
  'ui/icon_utils.cc',
  'ui/learning_dialogs.cc',
  'ui/checkpoint_view.cc',
  'ui/lesson_blocks.cc',
  'ui/outline_blocks.cc',
  'ui/learning_unit_view.cc',
  'ui/pocket_cube_page.cc',
  'ui/progress_overview.cc',
  'ui/quiz_dialog.cc',
  'ui/settings_dialog.cc',
  'ui/source_view.cc',
  'ui/type_semantics_lesson_page.cc',
)

# === 打包资源 ===
resources = gnome.compile_resources(
  'app-resources',
  gresource_xml,
  dependencies: compiled_ui + [runtime_catalog_generated],
  source_dir: ['resources', '.', meson.current_build_dir()]
)

executable('Athena', app_sources,
  sources: resources,
  include_directories: [cplusplus_inc],
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
  'resources/icons/16x16/apps/cn.athena.icon.png',
  install_dir: get_option('datadir') / 'icons/hicolor/16x16/apps'
)
install_data(
  'resources/icons/32x32/apps/cn.athena.icon.png',
  install_dir: get_option('datadir') / 'icons/hicolor/32x32/apps'
)
install_data(
  'resources/icons/64x64/apps/cn.athena.icon.png',
  install_dir: get_option('datadir') / 'icons/hicolor/64x64/apps'
)
install_data(
  'resources/icons/128x128/apps/cn.athena.icon.png',
  install_dir: get_option('datadir') / 'icons/hicolor/128x128/apps'
)
install_data(
  'resources/icons/256x256/apps/cn.athena.icon.png',
  install_dir: get_option('datadir') / 'icons/hicolor/256x256/apps'
)
install_data(
  'resources/icons/512x512/apps/cn.athena.icon.png',
  install_dir: get_option('datadir') / 'icons/hicolor/512x512/apps'
)
install_data(
  'resources/icons/1024x1024/apps/cn.athena.icon.png',
  install_dir: get_option('datadir') / 'icons/hicolor/1024x1024/apps'
)
install_data(
  'packaging/cn.yatiger.athena.desktop.in',
  # 短名。scripts/package_linux.py 按这个名字找它——两处必须一致，
  # 不一致时只有 Linux 发布会炸，平时的构建和测试都发现不了。
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
    'tests/case_runner_test.cc',
    'tests/case_workspace_test.cc',
    'tests/content_loader_test.cc',
    'tests/doc_model_test.cc',
    'tests/experiment_runner_test.cc',
    'tests/app_paths_test.cc',
    'tests/domain_graph_test.cc',
    'tests/function_registry_test.cc',
    'tests/knowledge_graph_test.cc',
    'tests/learning_store_test.cc',
    'tests/chart_scale_test.cc',
    'tests/pocket_cube_state_test.cc',
    'tests/pocket_cube_test.cc',
    'tests/progress_stats_test.cc',
    'tests/raii_content_test.cc',
    'tests/type_semantics_content_test.cc',
    'tests/source_locator_test.cc'
  ),
  sources: resources,
  include_directories: [cplusplus_inc],
  cpp_args: [test_source_root_arg],
  dependencies: [gtest_main_dep, athena_core_dep]
)
test('athena-core', core_test_exe)

# GTK 测试只检查 Blueprint/GResource 能否构造关键控件，不启动完整窗口。
gtk_test_exe = executable(
  'athena-gtk-tests',
  files(
    'tests/gtk_resource_test.cc',
    'tests/knowledge_graph_view_test.cc',
    'tests/progress_overview_test.cc',
    'tests/pocket_cube_view_test.cc',
    'practice/pocket_cube/view.cc',
    'render/cairo_text.cc',
    'render/chart_view.cc',
    'render/knowledge_graph_view.cc',
    'ui/progress_overview.cc'
  ),
  sources: resources,
  include_directories: [cplusplus_inc],
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
