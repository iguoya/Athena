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

/* 已知限制：LV_USE_TINY_TTF 在 Windows 上栅格化首个 CJK 字形会死锁
 * （Deng/simhei/msyh 都复现，疑似 stb_truetype 与大字体的问题），
 * 因此这里不开它，界面文本用英文。要中文需换 FreeType 集成。 */
#define LV_USE_TINY_TTF 0

#endif
