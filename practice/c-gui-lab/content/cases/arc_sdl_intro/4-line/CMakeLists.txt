cmake_minimum_required(VERSION 3.5)

project(4-line LANGUAGES C)


find_package(SDL2 REQUIRED)
include_directories(${SDL2_INCLUDE_DIRS})



add_executable(4-line main.c)


target_link_libraries(4-line ${SDL2_LIBRARIES})
