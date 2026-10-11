cmake_minimum_required(VERSION 3.21)
# exp.buttons —— 「按钮」章的骨架实验（ADR 0059：骨架可编译运行，学员只补 TODO）。
add_executable(exp-buttons src/main.cpp)
target_include_directories(exp-buttons PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_link_libraries(exp-buttons PRIVATE PkgConfig::GTKMM4)
