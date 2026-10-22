cmake_minimum_required(VERSION 3.5)

project(NodeClient LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

link_directories(../build-NodeLibrary-unknown-Debug/)

add_executable(NodeClient main.cpp client.h client.cpp)

target_link_libraries(NodeClient NodeLibrary)
