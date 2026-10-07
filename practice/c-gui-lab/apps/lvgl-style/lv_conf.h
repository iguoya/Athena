/* LVGL 精简配置：只写与 lv_conf_internal.h 默认值不同的项。 */
#ifndef LV_CONF_H
#define LV_CONF_H

#define LV_COLOR_DEPTH 32
#define LV_USE_OS LV_OS_NONE
#define LV_DEF_REFR_PERIOD 16

/* 桌面模拟用系统 malloc：内置静态池是嵌入式姿势，widgets 官方 demo 的对象量
 * 会把默认池耗尽，lv_obj_create 返回 NULL 后一路段错误（9.2.2 实测）。 */
#define LV_USE_STDLIB_MALLOC LV_STDLIB_CLIB

/* SDL2 模拟器后端（窗口与鼠标输入） */
#define LV_USE_SDL 1

/* 界面用到的内置字体 */
#define LV_FONT_MONTSERRAT_12 1
#define LV_FONT_MONTSERRAT_14 1
#define LV_FONT_MONTSERRAT_16 1
#define LV_FONT_MONTSERRAT_20 1
#define LV_FONT_MONTSERRAT_22 1
#define LV_FONT_MONTSERRAT_28 1
#define LV_FONT_DEFAULT &lv_font_montserrat_20

/* 官方 demos：9.3.0 的 lv_demo_widgets 在本机死锁；9.2.2（machine 同版本）
 * 实测见运行结果。 */
#define LV_USE_DEMO_WIDGETS 1

/* 中文显示用 lv_font_conv 预生成的子集字体（cjk_font.c），构建期编译进
 * 可执行文件，不需要任何运行时字体渲染器——tiny_ttf 与 FreeType 在这台
 * Windows 上都死在首个 CJK 字形（详见 cjk_font.h）。 */

#endif
