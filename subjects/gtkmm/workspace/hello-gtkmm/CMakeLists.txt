cmake_minimum_required(VERSION 3.21)
project(hello-gtkmm CXX)

# 与 demos/ 同一套工具链约定（gtkmm-4.0、C++17），但这里是学习者的自由练习区
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)

add_executable(hello-gtkmm src/main.cpp)
target_link_libraries(hello-gtkmm PRIVATE PkgConfig::GTKMM4)
