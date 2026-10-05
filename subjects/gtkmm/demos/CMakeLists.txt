cmake_minimum_required(VERSION 3.21)
project(athena-gtkmm-demos CXX)

# 每个演示/实验一个独立工程（应用 ADR 0001 决策 4），顶层只负责统一工具链。
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)

add_subdirectory(buttons)
add_subdirectory(buttons-lab)
