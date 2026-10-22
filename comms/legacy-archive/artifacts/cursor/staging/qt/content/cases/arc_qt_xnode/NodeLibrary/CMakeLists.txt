cmake_minimum_required(VERSION 3.14)

project(NodeLibrary LANGUAGES CXX)

set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(NodeLibrary SHARED
  NodeLibrary_global.h
  nodelibrary.cpp
  nodelibrary.h
  message.h message.cpp
  servernode.h servernode.cpp
)

target_compile_definitions(NodeLibrary PRIVATE NODELIBRARY_LIBRARY)
