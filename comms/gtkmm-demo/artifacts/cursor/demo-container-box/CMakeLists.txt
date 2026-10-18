cmake_minimum_required(VERSION 3.21)
# demo.container-box —— 第 9 章水平 Box：多余宽度分给谁。
add_executable(demo-container-box src/main.cpp)
target_include_directories(demo-container-box PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_link_libraries(demo-container-box PRIVATE PkgConfig::GTKMM4)
