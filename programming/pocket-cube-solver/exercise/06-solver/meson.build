project('cube-06', 'cpp',
  version: '0.1.0',
  default_options: ['cpp_std=c++20', 'warning_level=2', 'optimization=2'])

gtkmm_dep = dependency('gtkmm-4.0')
glib_dep = dependency('glib-2.0')
glibmm_dep = dependency('glibmm-2.68')

# 源文件是 UTF-8。Windows 上 gcc 默认按系统代码页读源文件，中文串会坏。
add_project_arguments('-finput-charset=UTF-8', language: 'cpp')

if glib_dep.version().version_compare('>= 2.89.2') and glibmm_dep.version().version_compare('< 2.89.0')
  add_project_arguments(
    '-include', meson.project_source_root() / 'compat' / 'glib_final_type_shim.h',
    language: 'cpp')
endif

blueprint_compiler = find_program('blueprint-compiler')
ui_file = custom_target(
  'window-ui',
  input: 'ui/window.blp',
  output: 'window.ui',
  command: [blueprint_compiler, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
  env: environment({'PYTHONUTF8': '1'}),
)
fs = import('fs')
css_file = fs.copyfile('ui/style.css')

gnome = import('gnome')
resources = gnome.compile_resources(
  'resources',
  'ui/app.gresource.xml',
  dependencies: [ui_file, css_file],
  source_dir: meson.current_build_dir(),
)

# 魔方模型与求解不依赖 GTK，窗口和测试各编一份。
core = ['cube.cc', 'solver.cc']

executable('cube-06', 'ui/main.cc', core, 'view.cc', 'session.cc', resources,
  dependencies: [gtkmm_dep],
  win_subsystem: 'windows',
  install: false)

core_test = executable('cube-test', 'cube_test.cc', core)
test('core', core_test, timeout: 120)
