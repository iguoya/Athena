# Athena · C 语言内存小程序（保留）。
#
# 教学入口已经改成上一级的 Qt Quick / QML 应用（ADR 0042）。本工程仍可
# 独立构建运行，主程序图谱不再 spawn 它。
cmake_minimum_required(VERSION 3.20)
project(AthenaC VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(athena-c
    src/main.c
    src/progress.c
)

# 学习库用系统自带的 libsqlite3，和主程序一致，不随包分发。
find_package(SQLite3 REQUIRED)
target_link_libraries(athena-c PRIVATE SQLite::SQLite3)

# 窗口后端：vendor/lvgl 与 SDL2 都就位才编真窗口，否则编占位实现。
# LVGL 只是"让 C 能开窗口"的手段，除本段和 src/ui/window_lvgl.c 之外，
# 代码里不应再出现这个名字。
set(LVGL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/lvgl")
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(SDL2 QUIET sdl2)
endif()

if(EXISTS "${LVGL_DIR}/lvgl.h" AND SDL2_FOUND)
    message(STATUS "窗口后端：LVGL + SDL2")
    # 配置头必须在 add_subdirectory 之前设好，LVGL 的 custom.cmake 会读它。
    set(LV_CONF_PATH "${CMAKE_CURRENT_SOURCE_DIR}/lv_conf.h" CACHE FILEPATH "" FORCE)
    add_subdirectory("${LVGL_DIR}" lvgl_build)
    target_sources(athena-c PRIVATE src/ui/window_lvgl.c src/cjk_font.c)
    target_include_directories(athena-c PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/vendor" ${SDL2_INCLUDE_DIRS})
    target_link_libraries(athena-c PRIVATE lvgl ${SDL2_LIBRARIES})
    target_link_directories(athena-c PRIVATE ${SDL2_LIBRARY_DIRS})
else()
    if(NOT EXISTS "${LVGL_DIR}/lvgl.h")
        message(STATUS "窗口后端：占位实现（vendor/lvgl 未就位，见 vendor/README.md）")
    else()
        message(STATUS "窗口后端：占位实现（未找到 SDL2）")
    endif()
    target_sources(athena-c PRIVATE src/ui/window_placeholder.c)
endif()
