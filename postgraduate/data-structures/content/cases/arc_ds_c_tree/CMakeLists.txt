cmake_minimum_required(VERSION 3.12)
project(tree C)

set(CMAKE_C_STANDARD 99)

add_executable(tree main.c)
target_link_libraries(tree m)

add_executable(advance_tree advance.c)
target_link_libraries(advance_tree m)
