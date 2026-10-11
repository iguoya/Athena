cmake_minimum_required(VERSION 3.21)
project(athena-gtkmm-workspace CXX)

# 顶层只统一工具链与产物落点（与 demos/CMakeLists.txt 同构）；
# 各学习集仍可独立构建：cmake -G Ninja -S <集> -B <集>/build
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)

# 新增学习集后在这里加一行；只想独立构建的集注释掉即可
add_subdirectory(hello-gtkmm)
