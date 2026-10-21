cmake_minimum_required(VERSION 3.12)
project(check C)

set(CMAKE_C_STANDARD 99)

add_executable(aa sub.c sub.h test_main.c unit_test.h test_sub.c)

target_link_libraries(aa check)