# raygui 官方控件演示（controls_test_suite）：单头文件库 + raylib 渲染。
# 源码 vendor 于 third_party/（raysan5/raygui@master），include 已就地修正。
add_executable(raygui-demo ${CMAKE_SOURCE_DIR}/third_party/raygui_controls_test.c)

find_package(PkgConfig REQUIRED)
pkg_check_modules(RAYLIB REQUIRED raylib)
target_include_directories(raygui-demo PRIVATE ${RAYLIB_INCLUDE_DIRS}
                                               ${CMAKE_SOURCE_DIR}/third_party)
target_link_directories(raygui-demo PRIVATE ${RAYLIB_LIBRARY_DIRS})
target_link_libraries(raygui-demo PRIVATE ${RAYLIB_LIBRARIES})
