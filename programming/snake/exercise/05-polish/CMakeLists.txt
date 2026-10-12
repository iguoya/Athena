cmake_minimum_required(VERSION 3.21)
project(snake-05-polish CXX)

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

add_executable(snake-05 src/main.cc)
target_link_libraries(snake-05 PRIVATE ${RAYLIB_TARGET})

# 蛇的规则不碰窗口，测试也就不需要 raylib——这是逻辑与渲染分离的直接回报。
enable_testing()
add_executable(snake-05-logic-test tests/logic_test.cc)
add_test(NAME snake-logic COMMAND snake-05-logic-test)
