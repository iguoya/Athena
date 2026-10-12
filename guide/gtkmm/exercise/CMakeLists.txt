cmake_minimum_required(VERSION 3.21)
project(athena-gtkmm-exercises CXX)

# 官方示例原样编译（应用 ADR 0006）：exercise/<示例集>/<示例>/ 是 upstream
# examples/book/ 的逐字镜像，构建脚本集中在本文件，不进镜像目录——与上游
# 对照用 `git diff --no-index exercise/<示例集> upstream/gtkmm-documentation/
# examples/book/<示例集>` 即得。产物统一落 build-exercise/，target 名 =
# content/demos.json 里 examples 实体 id 的 `.` 换 `-`（check.py 与壳按此
# 定位，与 demos 的 build-native 同一约定、不同产物目录）。各示例的源文件
# 清单取自上游 meson.build（官方构建的精确口径）；资源示例经
# glib-compile-resources 生成后一并编译（等价官方 gnome.compile_resources）。
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)
find_program(GLIB_COMPILE_RESOURCES NAMES glib-compile-resources REQUIRED)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/gen)

# —— buttons/（教程第 6 章示例集，ADR 0006 首批）——
add_executable(example-buttons-button
    buttons/button/main.cc
    buttons/button/buttons.cc
    buttons/button/buttons.h)
target_link_libraries(example-buttons-button PRIVATE PkgConfig::GTKMM4)

add_executable(example-buttons-togglebutton
    buttons/togglebutton/main.cc
    buttons/togglebutton/examplewindow.cc
    buttons/togglebutton/examplewindow.h)
target_link_libraries(example-buttons-togglebutton PRIVATE PkgConfig::GTKMM4)

add_executable(example-buttons-checkbutton
    buttons/checkbutton/main.cc
    buttons/checkbutton/examplewindow.cc
    buttons/checkbutton/examplewindow.h)
target_link_libraries(example-buttons-checkbutton PRIVATE PkgConfig::GTKMM4)

add_executable(example-buttons-radiobutton
    buttons/radiobutton/main.cc
    buttons/radiobutton/radiobuttons.cc
    buttons/radiobutton/radiobuttons.h)
target_link_libraries(example-buttons-radiobutton PRIVATE PkgConfig::GTKMM4)

add_executable(example-buttons-scalebutton
    buttons/scalebutton/main.cc
    buttons/scalebutton/examplewindow.cc
    buttons/scalebutton/examplewindow.h)
target_link_libraries(example-buttons-scalebutton PRIVATE PkgConfig::GTKMM4)

# —— range_widgets（第 7 章 Range Widgets） ——

# example.range_widgets —— 官方示例原样编译（源清单取自上游 meson：range_widgets）
add_executable(example-range_widgets
    range_widgets/examplewindow.cc
    range_widgets/main.cc
)
target_link_libraries(example-range_widgets PRIVATE PkgConfig::GTKMM4)

# —— label / entry / spinbutton 等（第 8 章 Miscellaneous Widgets） ——

# example.entry.completion —— 官方示例原样编译（源清单取自上游 meson：entry/completion）
add_executable(example-entry-completion
    entry/completion/examplewindow.cc
    entry/completion/main.cc
)
target_link_libraries(example-entry-completion PRIVATE PkgConfig::GTKMM4)

# example.entry.icon —— 官方示例原样编译（源清单取自上游 meson：entry/icon）
add_executable(example-entry-icon
    entry/icon/examplewindow.cc
    entry/icon/main.cc
)
target_link_libraries(example-entry-icon PRIVATE PkgConfig::GTKMM4)

# example.entry.progress —— 官方示例原样编译（源清单取自上游 meson：entry/progress）
add_executable(example-entry-progress
    entry/progress/examplewindow.cc
    entry/progress/main.cc
)
target_link_libraries(example-entry-progress PRIVATE PkgConfig::GTKMM4)

# example.entry.simple —— 官方示例原样编译（源清单取自上游 meson：entry/simple）
add_executable(example-entry-simple
    entry/simple/examplewindow.cc
    entry/simple/main.cc
)
target_link_libraries(example-entry-simple PRIVATE PkgConfig::GTKMM4)

# example.frame —— 官方示例原样编译（源清单取自上游 meson：frame）
add_executable(example-frame
    frame/examplewindow.cc
    frame/main.cc
)
target_link_libraries(example-frame PRIVATE PkgConfig::GTKMM4)

# example.infobar —— 官方示例原样编译（源清单取自上游 meson：infobar）
add_executable(example-infobar
    infobar/examplewindow.cc
    infobar/main.cc
)
target_link_libraries(example-infobar PRIVATE PkgConfig::GTKMM4)

# example.label —— 官方示例原样编译（源清单取自上游 meson：label）
add_executable(example-label
    label/examplewindow.cc
    label/main.cc
)
target_link_libraries(example-label PRIVATE PkgConfig::GTKMM4)

# example.progressbar —— 官方示例原样编译（源清单取自上游 meson：progressbar）
add_executable(example-progressbar
    progressbar/examplewindow.cc
    progressbar/main.cc
)
target_link_libraries(example-progressbar PRIVATE PkgConfig::GTKMM4)

# example.spinbutton —— 官方示例原样编译（源清单取自上游 meson：spinbutton）
add_executable(example-spinbutton
    spinbutton/examplewindow.cc
    spinbutton/main.cc
)
target_link_libraries(example-spinbutton PRIVATE PkgConfig::GTKMM4)

# example.tooltips —— 官方示例原样编译（源清单取自上游 meson：tooltips）
add_executable(example-tooltips
    tooltips/examplewindow.cc
    tooltips/main.cc
)
target_link_libraries(example-tooltips PRIVATE PkgConfig::GTKMM4)

# —— box / grid / listbox_flowbox 等（第 9 章 Container Widgets） ——

# example.actionbar —— 官方示例原样编译（源清单取自上游 meson：actionbar）
add_executable(example-actionbar
    actionbar/examplewindow.cc
    actionbar/main.cc
)
target_link_libraries(example-actionbar PRIVATE PkgConfig::GTKMM4)

# example.aspectframe —— 官方示例原样编译（源清单取自上游 meson：aspectframe）
add_executable(example-aspectframe
    aspectframe/examplewindow.cc
    aspectframe/main.cc
)
target_link_libraries(example-aspectframe PRIVATE PkgConfig::GTKMM4)

# example.assistant —— 官方示例原样编译（源清单取自上游 meson：assistant）
add_executable(example-assistant
    assistant/exampleassistant.cc
    assistant/examplewindow.cc
    assistant/main.cc
)
target_link_libraries(example-assistant PRIVATE PkgConfig::GTKMM4)

# example.box —— 官方示例原样编译（源清单取自上游 meson：box）
add_executable(example-box
    box/examplewindow.cc
    box/main.cc
    box/packbox.cc
)
target_link_libraries(example-box PRIVATE PkgConfig::GTKMM4)

# example.expander —— 官方示例原样编译（源清单取自上游 meson：expander）
add_executable(example-expander
    expander/examplewindow.cc
    expander/main.cc
)
target_link_libraries(example-expander PRIVATE PkgConfig::GTKMM4)

# example.grid —— 官方示例原样编译（源清单取自上游 meson：grid）
add_executable(example-grid
    grid/examplewindow.cc
    grid/main.cc
)
target_link_libraries(example-grid PRIVATE PkgConfig::GTKMM4)

# example.listbox_flowbox.flowbox —— 官方示例原样编译（源清单取自上游 meson：listbox_flowbox/flowbox）
add_executable(example-listbox_flowbox-flowbox
    listbox_flowbox/flowbox/examplewindow.cc
    listbox_flowbox/flowbox/main.cc
)
target_link_libraries(example-listbox_flowbox-flowbox PRIVATE PkgConfig::GTKMM4)

# example.listbox_flowbox.listbox —— 官方示例原样编译（源清单取自上游 meson：listbox_flowbox/listbox）
add_executable(example-listbox_flowbox-listbox
    listbox_flowbox/listbox/examplerow.cc
    listbox_flowbox/listbox/examplewindow.cc
    listbox_flowbox/listbox/main.cc
)
target_link_libraries(example-listbox_flowbox-listbox PRIVATE PkgConfig::GTKMM4)

# example.listbox_flowbox.listmodel —— 官方示例原样编译（源清单取自上游 meson：listbox_flowbox/listmodel）
add_executable(example-listbox_flowbox-listmodel
    listbox_flowbox/listmodel/examplewindow.cc
    listbox_flowbox/listmodel/main.cc
    listbox_flowbox/listmodel/myobject.cc
)
target_link_libraries(example-listbox_flowbox-listmodel PRIVATE PkgConfig::GTKMM4)

# example.notebook —— 官方示例原样编译（源清单取自上游 meson：notebook）
add_executable(example-notebook
    notebook/examplewindow.cc
    notebook/main.cc
)
target_link_libraries(example-notebook PRIVATE PkgConfig::GTKMM4)

# example.paned —— 官方示例原样编译（源清单取自上游 meson：paned）
add_executable(example-paned
    paned/examplewindow.cc
    paned/main.cc
    paned/messageslist.cc
    paned/messagetext.cc
)
target_link_libraries(example-paned PRIVATE PkgConfig::GTKMM4)

# example.popover —— 官方示例原样编译（源清单取自上游 meson：popover）
add_executable(example-popover
    popover/examplewindow.cc
    popover/main.cc
)
target_link_libraries(example-popover PRIVATE PkgConfig::GTKMM4)

# example.scrolledwindow —— 官方示例原样编译（源清单取自上游 meson：scrolledwindow）
add_executable(example-scrolledwindow
    scrolledwindow/examplewindow.cc
    scrolledwindow/main.cc
)
target_link_libraries(example-scrolledwindow PRIVATE PkgConfig::GTKMM4)

# —— listmodelviews（第 10 章 ListView, GridView, ColumnView） ——

# example.listmodelviews.editable_cells —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/editable_cells）
add_executable(example-listmodelviews-editable_cells
    listmodelviews/editable_cells/examplewindow.cc
    listmodelviews/editable_cells/main.cc
)
target_link_libraries(example-listmodelviews-editable_cells PRIVATE PkgConfig::GTKMM4)

# example.listmodelviews.filter —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/filter）
add_executable(example-listmodelviews-filter
    listmodelviews/filter/examplewindow.cc
    listmodelviews/filter/main.cc
)
target_link_libraries(example-listmodelviews-filter PRIVATE PkgConfig::GTKMM4)

# example.listmodelviews.gridview —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/gridview）
add_executable(example-listmodelviews-gridview
    listmodelviews/gridview/examplewindow.cc
    listmodelviews/gridview/main.cc
)
target_link_libraries(example-listmodelviews-gridview PRIVATE PkgConfig::GTKMM4)

# example.listmodelviews.list_columnview —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/list_columnview）
add_executable(example-listmodelviews-list_columnview
    listmodelviews/list_columnview/examplewindow.cc
    listmodelviews/list_columnview/main.cc
)
target_link_libraries(example-listmodelviews-list_columnview PRIVATE PkgConfig::GTKMM4)

# example.listmodelviews.list_listview —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/list_listview）
add_executable(example-listmodelviews-list_listview
    listmodelviews/list_listview/examplewindow.cc
    listmodelviews/list_listview/main.cc
)
target_link_libraries(example-listmodelviews-list_listview PRIVATE PkgConfig::GTKMM4)

# example.listmodelviews.sort —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/sort）
add_executable(example-listmodelviews-sort
    listmodelviews/sort/examplewindow.cc
    listmodelviews/sort/main.cc
)
target_link_libraries(example-listmodelviews-sort PRIVATE PkgConfig::GTKMM4)

# example.listmodelviews.tree_columnview —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/tree_columnview）
add_executable(example-listmodelviews-tree_columnview
    listmodelviews/tree_columnview/examplewindow.cc
    listmodelviews/tree_columnview/main.cc
)
target_link_libraries(example-listmodelviews-tree_columnview PRIVATE PkgConfig::GTKMM4)

# example.listmodelviews.tree_listview —— 官方示例原样编译（源清单取自上游 meson：listmodelviews/tree_listview）
add_executable(example-listmodelviews-tree_listview
    listmodelviews/tree_listview/examplewindow.cc
    listmodelviews/tree_listview/main.cc
)
target_link_libraries(example-listmodelviews-tree_listview PRIVATE PkgConfig::GTKMM4)

# —— dropdown（第 12 章 DropDown） ——

# example.dropdown.complex —— 官方示例原样编译（源清单取自上游 meson：dropdown/complex）
add_executable(example-dropdown-complex
    dropdown/complex/examplewindow.cc
    dropdown/complex/main.cc
)
target_link_libraries(example-dropdown-complex PRIVATE PkgConfig::GTKMM4)

# example.dropdown.search_font —— 官方示例原样编译（源清单取自上游 meson：dropdown/search_font）
add_executable(example-dropdown-search_font
    dropdown/search_font/examplewindow.cc
    dropdown/search_font/main.cc
)
target_link_libraries(example-dropdown-search_font PRIVATE PkgConfig::GTKMM4)

# example.dropdown.search_string —— 官方示例原样编译（源清单取自上游 meson：dropdown/search_string）
add_executable(example-dropdown-search_string
    dropdown/search_string/examplewindow.cc
    dropdown/search_string/main.cc
)
target_link_libraries(example-dropdown-search_string PRIVATE PkgConfig::GTKMM4)

# example.dropdown.string —— 官方示例原样编译（源清单取自上游 meson：dropdown/string）
add_executable(example-dropdown-string
    dropdown/string/examplewindow.cc
    dropdown/string/main.cc
)
target_link_libraries(example-dropdown-string PRIVATE PkgConfig::GTKMM4)

# —— combobox（第 13 章 Combo Boxes） ——

# example.combobox.complex —— 官方示例原样编译（源清单取自上游 meson：combobox/complex）
add_executable(example-combobox-complex
    combobox/complex/examplewindow.cc
    combobox/complex/main.cc
)
target_link_libraries(example-combobox-complex PRIVATE PkgConfig::GTKMM4)

# example.combobox.entry_complex —— 官方示例原样编译（源清单取自上游 meson：combobox/entry_complex）
add_executable(example-combobox-entry_complex
    combobox/entry_complex/examplewindow.cc
    combobox/entry_complex/main.cc
)
target_link_libraries(example-combobox-entry_complex PRIVATE PkgConfig::GTKMM4)

# example.combobox.entry_text —— 官方示例原样编译（源清单取自上游 meson：combobox/entry_text）
add_executable(example-combobox-entry_text
    combobox/entry_text/examplewindow.cc
    combobox/entry_text/main.cc
)
target_link_libraries(example-combobox-entry_text PRIVATE PkgConfig::GTKMM4)

# example.combobox.text —— 官方示例原样编译（源清单取自上游 meson：combobox/text）
add_executable(example-combobox-text
    combobox/text/examplewindow.cc
    combobox/text/main.cc
)
target_link_libraries(example-combobox-text PRIVATE PkgConfig::GTKMM4)

# —— textview（第 14 章 TextView） ——

# example.textview —— 官方示例原样编译（源清单取自上游 meson：textview）
add_executable(example-textview
    textview/examplewindow.cc
    textview/main.cc
)
target_link_libraries(example-textview PRIVATE PkgConfig::GTKMM4)

# —— menus / menus_and_toolbars（第 15 章 Menus and Toolbars） ——

# example.menus.main_menu —— 官方示例原样编译（源清单取自上游 meson：menus/main_menu）
add_executable(example-menus-main_menu
    menus/main_menu/exampleapplication.cc
    menus/main_menu/examplewindow.cc
    menus/main_menu/main.cc
)
target_link_libraries(example-menus-main_menu PRIVATE PkgConfig::GTKMM4)

# example.menus.popup —— 官方示例原样编译（源清单取自上游 meson：menus/popup）
add_executable(example-menus-popup
    menus/popup/examplewindow.cc
    menus/popup/main.cc
)
target_link_libraries(example-menus-popup PRIVATE PkgConfig::GTKMM4)

# example.menus_and_toolbars —— 官方示例原样编译（源清单取自上游 meson：menus_and_toolbars）
set_source_files_properties(${CMAKE_BINARY_DIR}/gen/example_menus_and_toolbars_resources.c PROPERTIES GENERATED TRUE)
add_custom_command(
    OUTPUT ${CMAKE_BINARY_DIR}/gen/example_menus_and_toolbars_resources.c
    COMMAND ${GLIB_COMPILE_RESOURCES} --sourcedir=${CMAKE_CURRENT_SOURCE_DIR}/menus_and_toolbars --generate-source --target=${CMAKE_BINARY_DIR}/gen/example_menus_and_toolbars_resources.c ${CMAKE_CURRENT_SOURCE_DIR}/menus_and_toolbars/toolbar.gresource.xml
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/menus_and_toolbars/toolbar.gresource.xml
    COMMENT "glib-compile-resources: example.menus_and_toolbars")
add_executable(example-menus_and_toolbars
    menus_and_toolbars/examplewindow.cc
    menus_and_toolbars/main.cc
    ${CMAKE_BINARY_DIR}/gen/example_menus_and_toolbars_resources.c
)
target_link_libraries(example-menus_and_toolbars PRIVATE PkgConfig::GTKMM4)

# —— dialogs（第 17 章 Dialogs） ——

# example.dialogs.aboutdialog —— 官方示例原样编译（源清单取自上游 meson：dialogs/aboutdialog）
set_source_files_properties(${CMAKE_BINARY_DIR}/gen/example_dialogs_aboutdialog_resources.c PROPERTIES GENERATED TRUE)
add_custom_command(
    OUTPUT ${CMAKE_BINARY_DIR}/gen/example_dialogs_aboutdialog_resources.c
    COMMAND ${GLIB_COMPILE_RESOURCES} --sourcedir=${CMAKE_CURRENT_SOURCE_DIR}/dialogs/aboutdialog --generate-source --target=${CMAKE_BINARY_DIR}/gen/example_dialogs_aboutdialog_resources.c ${CMAKE_CURRENT_SOURCE_DIR}/dialogs/aboutdialog/aboutdialog.gresource.xml
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/dialogs/aboutdialog/aboutdialog.gresource.xml
    COMMENT "glib-compile-resources: example.dialogs.aboutdialog")
add_executable(example-dialogs-aboutdialog
    dialogs/aboutdialog/examplewindow.cc
    dialogs/aboutdialog/main.cc
    ${CMAKE_BINARY_DIR}/gen/example_dialogs_aboutdialog_resources.c
)
target_link_libraries(example-dialogs-aboutdialog PRIVATE PkgConfig::GTKMM4)

# example.dialogs.alertdialog —— 官方示例原样编译（源清单取自上游 meson：dialogs/alertdialog）
add_executable(example-dialogs-alertdialog
    dialogs/alertdialog/examplewindow.cc
    dialogs/alertdialog/main.cc
)
target_link_libraries(example-dialogs-alertdialog PRIVATE PkgConfig::GTKMM4)

# example.dialogs.colordialog —— 官方示例原样编译（源清单取自上游 meson：dialogs/colordialog）
add_executable(example-dialogs-colordialog
    dialogs/colordialog/examplewindow.cc
    dialogs/colordialog/main.cc
)
target_link_libraries(example-dialogs-colordialog PRIVATE PkgConfig::GTKMM4)

# example.dialogs.filedialog —— 官方示例原样编译（源清单取自上游 meson：dialogs/filedialog）
add_executable(example-dialogs-filedialog
    dialogs/filedialog/examplewindow.cc
    dialogs/filedialog/main.cc
)
target_link_libraries(example-dialogs-filedialog PRIVATE PkgConfig::GTKMM4)

# example.dialogs.fontdialog —— 官方示例原样编译（源清单取自上游 meson：dialogs/fontdialog）
add_executable(example-dialogs-fontdialog
    dialogs/fontdialog/examplewindow.cc
    dialogs/fontdialog/main.cc
)
target_link_libraries(example-dialogs-fontdialog PRIVATE PkgConfig::GTKMM4)

# example.dialogs.windowdialog —— 官方示例原样编译（源清单取自上游 meson：dialogs/windowdialog）
add_executable(example-dialogs-windowdialog
    dialogs/windowdialog/examplewindow.cc
    dialogs/windowdialog/main.cc
    dialogs/windowdialog/namedialog.cc
)
target_link_libraries(example-dialogs-windowdialog PRIVATE PkgConfig::GTKMM4)


# —— treeview（第 11 章 TreeView）——


# example.treeview.combo_renderer —— 官方示例原样编译（源清单取自上游 meson：treeview/combo_renderer）
add_executable(example-treeview-combo_renderer
    treeview/combo_renderer/examplewindow.cc
    treeview/combo_renderer/main.cc
)
target_link_libraries(example-treeview-combo_renderer PRIVATE PkgConfig::GTKMM4)


# example.treeview.custom_treemodel —— 官方示例原样编译（源清单取自上游 meson：treeview/custom_treemodel）
add_executable(example-treeview-custom_treemodel
    treeview/custom_treemodel/exampletreemodel.cc
    treeview/custom_treemodel/examplewindow.cc
    treeview/custom_treemodel/main.cc
)
target_link_libraries(example-treeview-custom_treemodel PRIVATE PkgConfig::GTKMM4)
# 上游这份示例把行号整型存进 user_data 指针再转回（32 位时代写法），64 位下
# 该转换默认报错；代码原样，只在构建端放宽检查。
target_compile_options(example-treeview-custom_treemodel PRIVATE $<$<CXX_COMPILER_ID:GNU,Clang>:-fpermissive>)


# example.treeview.drag_and_drop —— 官方示例原样编译（源清单取自上游 meson：treeview/drag_and_drop）
add_executable(example-treeview-drag_and_drop
    treeview/drag_and_drop/examplewindow.cc
    treeview/drag_and_drop/main.cc
    treeview/drag_and_drop/treemodel_dnd.cc
)
target_link_libraries(example-treeview-drag_and_drop PRIVATE PkgConfig::GTKMM4)


# example.treeview.editable_cells —— 官方示例原样编译（源清单取自上游 meson：treeview/editable_cells）
add_executable(example-treeview-editable_cells
    treeview/editable_cells/examplewindow.cc
    treeview/editable_cells/main.cc
)
target_link_libraries(example-treeview-editable_cells PRIVATE PkgConfig::GTKMM4)


# example.treeview.filter —— 官方示例原样编译（源清单取自上游 meson：treeview/filter）
add_executable(example-treeview-filter
    treeview/filter/examplewindow.cc
    treeview/filter/main.cc
)
target_link_libraries(example-treeview-filter PRIVATE PkgConfig::GTKMM4)


# example.treeview.filter_modify —— 官方示例原样编译（源清单取自上游 meson：treeview/filter_modify）
add_executable(example-treeview-filter_modify
    treeview/filter_modify/examplewindow.cc
    treeview/filter_modify/main.cc
)
target_link_libraries(example-treeview-filter_modify PRIVATE PkgConfig::GTKMM4)


# example.treeview.list —— 官方示例原样编译（源清单取自上游 meson：treeview/list）
add_executable(example-treeview-list
    treeview/list/examplewindow.cc
    treeview/list/main.cc
)
target_link_libraries(example-treeview-list PRIVATE PkgConfig::GTKMM4)


# example.treeview.listviewtext —— 官方示例原样编译（源清单取自上游 meson：treeview/listviewtext）
add_executable(example-treeview-listviewtext
    treeview/listviewtext/examplewindow.cc
    treeview/listviewtext/main.cc
)
target_link_libraries(example-treeview-listviewtext PRIVATE PkgConfig::GTKMM4)


# example.treeview.modelsort —— 官方示例原样编译（源清单取自上游 meson：treeview/modelsort）
add_executable(example-treeview-modelsort
    treeview/modelsort/examplewindow.cc
    treeview/modelsort/main.cc
)
target_link_libraries(example-treeview-modelsort PRIVATE PkgConfig::GTKMM4)


# example.treeview.popup —— 官方示例原样编译（源清单取自上游 meson：treeview/popup）
add_executable(example-treeview-popup
    treeview/popup/examplewindow.cc
    treeview/popup/main.cc
    treeview/popup/treeview_withpopup.cc
)
target_link_libraries(example-treeview-popup PRIVATE PkgConfig::GTKMM4)


# example.treeview.tree —— 官方示例原样编译（源清单取自上游 meson：treeview/tree）
add_executable(example-treeview-tree
    treeview/tree/examplewindow.cc
    treeview/tree/main.cc
)
target_link_libraries(example-treeview-tree PRIVATE PkgConfig::GTKMM4)
