cmake_minimum_required(VERSION 3.21)
project(snake-02-grid CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(raylib QUIET)
if(raylib_FOUND)
  set(RAYLIB_TARGET raylib)
else()
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(RAYLIB REQUIRED IMPORTED_TARGET raylib)
  set(RAYLIB_TARGET PkgConfig::RAYLIB)
endif()

add_executable(snake-02 src/main.cc)
target_link_libraries(snake-02 PRIVATE ${RAYLIB_TARGET})
