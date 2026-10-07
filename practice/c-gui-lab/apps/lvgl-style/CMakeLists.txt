set(LVGL ${CMAKE_SOURCE_DIR}/third_party/lvgl)

# LVGL 全量编译为静态库；SDL 驱动由 lv_conf.h 的 LV_USE_SDL 打开
file(GLOB_RECURSE LVGL_SOURCES CONFIGURE_DEPENDS ${LVGL}/src/*.c)
add_library(lvgl_ext STATIC ${LVGL_SOURCES})
target_include_directories(lvgl_ext PUBLIC ${LVGL} ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(lvgl_ext PUBLIC LV_CONF_INCLUDE_SIMPLE)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED sdl2)
target_include_directories(lvgl_ext PUBLIC ${SDL2_INCLUDE_DIRS})
target_compile_options(lvgl_ext PRIVATE ${SDL2_CFLAGS_OTHER})

add_executable(lvgl-style lvgl_style.c)
target_link_libraries(lvgl-style PRIVATE lvgl_ext ${SDL2_LIBRARIES})
target_include_directories(lvgl-style PRIVATE ${SDL2_INCLUDE_DIRS} ${LVGL})
target_link_directories(lvgl-style PRIVATE ${SDL2_LIBRARY_DIRS})
