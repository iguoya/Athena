project('chess-01', 'cpp',
  version: '0.1.0',
  default_options: ['cpp_std=c++20', 'warning_level=2'])

gtkmm_dep = dependency('gtkmm-4.0')
glib_dep = dependency('glib-2.0')
glibmm_dep = dependency('glibmm-2.68')
add_project_arguments('-finput-charset=UTF-8', language: 'cpp')
if glib_dep.version().version_compare('>= 2.89.2') and glibmm_dep.version().version_compare('< 2.89.0')
  add_project_arguments('-include', meson.project_source_root() / 'compat' / 'glib_final_type_shim.h', language: 'cpp')
endif

blueprint_compiler = find_program('blueprint-compiler')
# blueprint-compiler 用 Python 读源文件。Windows 默认代码页不是 UTF-8，中文界面会读坏。
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

executable('chess-01-code', 'code/main.cc',
  dependencies: [gtkmm_dep],
  win_subsystem: 'windows',
  install: false)
executable('chess-01-ui', 'ui/main.cc', resources,
  dependencies: [gtkmm_dep],
  win_subsystem: 'windows',
  install: false)
