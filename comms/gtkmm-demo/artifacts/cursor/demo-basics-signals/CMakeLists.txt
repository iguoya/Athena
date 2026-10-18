cmake_minimum_required(VERSION 3.21)
# demo.basics-signals —— 第 3 章信号时序：两个 clicked 处理器 + 窗口生命周期。
add_executable(demo-basics-signals src/main.cpp)
target_include_directories(demo-basics-signals PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_link_libraries(demo-basics-signals PRIVATE PkgConfig::GTKMM4)
