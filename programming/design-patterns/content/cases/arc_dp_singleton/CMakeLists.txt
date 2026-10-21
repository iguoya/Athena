cmake_minimum_required(VERSION 3.5)

project(Singleton)


set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

AUX_SOURCE_DIRECTORY(. DIR_SRCS)

add_executable(Singleton ${DIR_SRCS})
