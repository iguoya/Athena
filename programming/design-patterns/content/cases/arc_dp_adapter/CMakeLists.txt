cmake_minimum_required(VERSION 2.8)

project(Adapter)


set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

AUX_SOURCE_DIRECTORY(. DIR_SRCS)

add_executable(Adapter ${DIR_SRCS})
