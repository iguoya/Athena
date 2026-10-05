cmake_minimum_required(VERSION 3.21)
# demo.buttons —— Buttons 章的真机演示：三种按钮 + 信号上报。
add_executable(demo-buttons src/main.cpp)
target_include_directories(demo-buttons PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_link_libraries(demo-buttons PRIVATE PkgConfig::GTKMM4)
