cmake_minimum_required(VERSION 3.5)

project(113-human-evolved LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

aux_source_directory(. DIR_SRCS)

add_executable(${PROJECT_NAME} ${DIR_SRCS})
#add_executable(113-human-evolved main.cpp)
