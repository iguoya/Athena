project('PracticePocketCube', 'cpp',
  version: '0.1.0',
  default_options: ['cpp_std=c++20'])

gnome = import('gnome')

gtkmm_dep = dependency('gtkmm-4.0')
gtk4_dep = dependency('gtk4')
glib_dep = dependency('glib-2.0')
glibmm_dep = dependency('glibmm-2.68')
sourceview_dep = dependency('gtksourceview-5')

# glib 2.89.2+ 与 glibmm < 2.89.0 的声明方式冲突，跟 apps/cpp 踩的是同一个坑
# （见 compat/glib_final_type_shim.h 顶部注释），这里复制一份同样的垫片，
# 不 include 那边的头文件。
if glib_dep.version().version_compare('>= 2.89.2') and glibmm_dep.version().version_compare('< 2.89.0')
  add_project_arguments(
    '-include', meson.project_source_root() / 'compat' / 'glib_final_type_shim.h',
    language: 'cpp')
endif
blueprint_compiler = find_program('blueprint-compiler')
blueprint_env = environment()
blueprint_env.set('PYTHONUTF8', '1')

# #include "pocket_cube/state.h" 这种写法是相对 apps/practice/（本文件所在
# 目录的上一级）解析的，跟 apps/cpp 的 include_directories(cplusplus_inc)
# 同一个道理——留了这层前缀，以后 apps/practice/ 下再加别的小项目时，各自
# 头文件不会因为都叫 state.h/view.h 之类的名字互相冲突。
practice_root = include_directories('..')

compiled_ui = custom_target(
  'compile-window.blp',
  input: files('window.blp'),
  output: 'window.ui',
  command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
  env: blueprint_env,
)

resources = gnome.compile_resources(
  'app-resources',
  'app.gresource.xml',
  dependencies: [compiled_ui],
  source_dir: [meson.current_build_dir()],
)

executable('pocket-cube', 'main.cc', 'state.cc', 'view.cc', resources,
  include_directories: [practice_root],
  cpp_args: ['-DPOCKET_CUBE_SOURCE_ROOT="' + meson.current_source_dir() + '"'],
  dependencies: [gtkmm_dep, gtk4_dep, sourceview_dep],
  install: false)
