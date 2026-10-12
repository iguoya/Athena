cmake_minimum_required(VERSION 3.21)
project(snake-01-window CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# raylib 的三种来源都提供 CMake 包配置（MSYS2 pacman、vcpkg、源码安装）；
# 个别发行版只装了 pkg-config 文件，落到底线再走一次 pkg_check_modules。
find_package(raylib QUIET)
if(raylib_FOUND)
  set(RAYLIB_TARGET raylib)
else()
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(RAYLIB REQUIRED IMPORTED_TARGET raylib)
  set(RAYLIB_TARGET PkgConfig::RAYLIB)
endif()

add_executable(snake-01 src/main.cc)
target_link_libraries(snake-01 PRIVATE ${RAYLIB_TARGET})
