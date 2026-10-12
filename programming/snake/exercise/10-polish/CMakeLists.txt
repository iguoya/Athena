cmake_minimum_required(VERSION 3.21)
project(snake-10-polish CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 源文件是 UTF-8；MSVC 默认按系统代码页读，中文注释会吞掉换行。
if(MSVC)
  add_compile_options(/utf-8)
endif()

# 系统 raylib 优先（MSYS2 / vcpkg / 发行版包）；没有就地拉源码自己编——
# raylib 是单文件 C 库，几秒编完。因此这门课不要求预先安装任何图形库。
find_package(raylib QUIET)
if(NOT raylib_FOUND)
  include(FetchContent)
  FetchContent_Declare(raylib
    GIT_REPOSITORY https://github.com/raysan5/raylib.git
    GIT_TAG 5.5
    GIT_SHALLOW TRUE)
  FetchContent_MakeAvailable(raylib)
endif()

add_executable(snake-10 src/main.cc)
set_target_properties(snake-10 PROPERTIES RUNTIME_OUTPUT_DIRECTORY "$<1:${CMAKE_CURRENT_BINARY_DIR}>")
target_link_libraries(snake-10 PRIVATE raylib)
# 规则不碰窗口，测试也就不需要 raylib——这是逻辑与渲染分离的直接回报。
enable_testing()
add_executable(snake-10-logic-test tests/logic_test.cc)
add_test(NAME snake-logic COMMAND $<TARGET_FILE:snake-10-logic-test>)

# 按需求编号铺开的规则验证（docs/design/overview.md 的追溯矩阵）。同样不链接 raylib。
add_executable(snake-10-rules-test tests/rules_test.cc)
add_test(NAME snake-rules COMMAND $<TARGET_FILE:snake-10-rules-test>)
