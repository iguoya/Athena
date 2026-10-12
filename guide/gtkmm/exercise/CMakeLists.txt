cmake_minimum_required(VERSION 3.21)
project(athena-gtkmm-exercises CXX)

# 官方示例原样编译（应用 ADR 0006）：exercise/<示例集>/<示例>/ 是 upstream
# examples/book/ 的逐字镜像，构建脚本集中在本文件，不进镜像目录——与上游
# 对照用 `git diff --no-index exercise/buttons upstream/gtkmm-documentation/
# examples/book/buttons` 即得。产物统一落 build-exercise/，target 名 =
# content/demos.json 里 examples 实体 id 的 `.` 换 `-`（check.py 与壳按此
# 定位，与 demos 的 build-native 同一约定、不同产物目录）。
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

# —— buttons/（教程第 6 章示例集）——
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
