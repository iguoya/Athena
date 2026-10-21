cmake_minimum_required(VERSION 3.12)
project(magic_square C)

set(CMAKE_C_STANDARD 99)

add_executable(magic_square main.c matrix.h matrix.c)
add_executable(unix_test unit_test_main.c matrix.h matrix.c)

target_link_libraries(magic_square m)
target_link_libraries(unix_test check m)