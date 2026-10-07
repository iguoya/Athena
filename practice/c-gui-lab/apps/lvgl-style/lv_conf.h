/* LVGL 精简配置：只写与 lv_conf_internal.h 默认值不同的项。 */
#ifndef LV_CONF_H
#define LV_CONF_H

#define LV_COLOR_DEPTH 32
#define LV_USE_OS LV_OS_NONE
#define LV_DEF_REFR_PERIOD 16

/* SDL2 模拟器后端（窗口与鼠标输入） */
#define LV_USE_SDL 1

/* 界面用到的内置字体 */
#define LV_FONT_MONTSERRAT_16 1
#define LV_FONT_MONTSERRAT_20 1
#define LV_FONT_MONTSERRAT_28 1
#define LV_FONT_DEFAULT &lv_font_montserrat_20

/* 中文显示用 lv_font_conv 预生成的子集字体（cjk_font.c），构建期编译进
 * 可执行文件，不需要任何运行时字体渲染器——tiny_ttf 与 FreeType 在这台
 * Windows 上都死在首个 CJK 字形（详见 cjk_font.h）。 */

#endif
