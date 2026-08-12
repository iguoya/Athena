project('Athena', 'cpp',
  version: '0.1',
  default_options: ['cpp_std=c++17'])

fs = import('fs')
gnome = import('gnome')

gtkmm_dep = dependency('gtkmm-4.0')
glib_dep = dependency('glib-2.0')
blueprint_compiler = find_program('blueprint-compiler')
# 步骤 1: 编译 Blueprint 文件
# 定义一个自定义目标，将所有 .blp 文件编译为 .ui 文件
compiled_ui = []
ui_blp_files = files(
  'resources/ui/window.blp',
  'resources/ui/chapters/welcome.blp',
  'resources/ui/chapters/functions.blp',
  'resources/ui/chapters/basic_syntax.blp',
)
foreach blp_file : ui_blp_files
  ui_file = fs.stem(blp_file) + '.ui'
  compiled_ui += custom_target(
    'compile-' + fs.name(blp_file),
    input: blp_file,
    output: ui_file,
    command: [blueprint_compiler, 'compile', '@INPUT@', '--output', '@OUTPUT@'],
   
  )
endforeach

src_files = files(
  'main.cc',
  'athena.cc',
  'mainwindow.cc'
)
# 定义要打包的资源列表
# meson.project_source_root() 确保路径是相对项目根目录的
resources = gnome.compile_resources(
  'app-resources',
  'resources/app.gresource.xml',
  dependencies: compiled_ui,
  source_dir: ['resources', '.']
)

executable('Athena', src_files,
  sources: resources,  
  dependencies: [
    gtkmm_dep,
    glib_dep
  ],
  install: true)