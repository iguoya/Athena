# LVGL 9.2.2（与 machine 学科 vendor 的版本对齐）：官方 demos 一并编译。
# 9.3.0 的 lv_demo_widgets 在本机死锁，9.2.2 是否复现见运行验证。
set(LVGL ${CMAKE_SOURCE_DIR}/third_party/lvgl-9.2.2)
file(GLOB_RECURSE LVGL_SOURCES CONFIGURE_DEPENDS ${LVGL}/src/*.c ${LVGL}/demos/*.c)
add_library(lvgl_ext STATIC ${LVGL_SOURCES})
target_include_directories(lvgl_ext PUBLIC ${LVGL} ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(lvgl_ext PUBLIC LV_CONF_INCLUDE_SIMPLE)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED sdl2)
target_include_directories(lvgl_ext PUBLIC ${SDL2_INCLUDE_DIRS})
target_compile_options(lvgl_ext PRIVATE ${SDL2_CFLAGS_OTHER})

add_executable(lvgl-style lvgl_style.c cjk_font.c font_cn_20.c font_cn_28.c)
target_link_libraries(lvgl-style PRIVATE lvgl_ext ${SDL2_LIBRARIES})
target_include_directories(lvgl-style PRIVATE ${SDL2_INCLUDE_DIRS} ${LVGL}
  ${CMAKE_SOURCE_DIR}/third_party) # 生成的 font_cn_*.c include "lvgl/lvgl.h"
target_link_directories(lvgl-style PRIVATE ${SDL2_LIBRARY_DIRS})
