cmake_minimum_required(VERSION 3.21)
project(example-buttons-scalebutton CXX)

# 官方示例的学习者副本（应用 ADR 0009）：源文件来自 exercise/ 镜像原样，
# 本文件由壳生成——改坏了删掉副本目录，在课程里重新点「打开工作区」即可。
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

add_executable(example-buttons-scalebutton
    examplewindow.cc
    examplewindow.h
    main.cc)
target_link_libraries(example-buttons-scalebutton PRIVATE PkgConfig::GTKMM4)
