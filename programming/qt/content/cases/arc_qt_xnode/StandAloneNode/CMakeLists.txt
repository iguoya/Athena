cmake_minimum_required(VERSION 3.5)

project(StandAloneNode LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
link_directories(../build-NodeLibrary-unknown-Debug/)

add_executable(StandAloneNode main.cpp)
target_link_libraries(StandAloneNode NodeLibrary)

install(TARGETS StandAloneNode
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
