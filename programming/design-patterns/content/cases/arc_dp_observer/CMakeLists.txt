cmake_minimum_required(VERSION 3.5)

project(Observer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

AUX_SOURCE_DIRECTORY(. DIR_SRCS)

add_executable(Observer ${DIR_SRCS})
