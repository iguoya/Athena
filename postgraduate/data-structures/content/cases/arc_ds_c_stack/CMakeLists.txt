cmake_minimum_required(VERSION 3.12)
project(stack C)

set(CMAKE_C_STANDARD 99)


add_executable(stack main.c)
add_executable(number_system_conversion number_system_conversion.c stack.h)
add_executable(symbol_matching symbol_matching.c stack.h)