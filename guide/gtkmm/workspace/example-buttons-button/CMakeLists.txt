cmake_minimum_required(VERSION 3.21)
project(example-buttons-button CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
add_executable(example-buttons-button
    main.cc
    buttons.cc
    buttons.h)
target_link_libraries(example-buttons-button PRIVATE PkgConfig::GTKMM4)
