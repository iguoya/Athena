#ifndef ATHENA_C_GUI_LAB_CJK_FONT_H
#define ATHENA_C_GUI_LAB_CJK_FONT_H

#include "lvgl.h"

// 界面中文字体：lv_font_conv 从黑体（simhei.ttf）离线生成的子集
// （界面全部汉字 + ASCII，20/28 两档），见 scripts/gen-cjk-font.sh。
//
// 为什么用预生成而不是运行时渲染：tiny_ttf 在这台 Windows 上栅格化首个
// CJK 字形就死循环（data/file 模式都复现，subjects/machine 的 create_data
// 方案在 mac/Linux 成熟但同样过不去），FreeType 集成同样卡死。
// 预生成子集是 LVGL 社区的标准做法：零运行时依赖、行为确定；样式橱窗
// 文本固定，子集也小（~200KB 源码）。文本变了重新跑生成脚本即可。

typedef struct {
    const lv_font_t* body;  // 正文字号
    const lv_font_t* title; // 标题字号
    const char* path;       // 生成来源，便于排查
} CjkFont;

// 返回预生成字体，不会失败（字体已编译进可执行文件）。
CjkFont cjk_font_load(void);
void cjk_font_free(CjkFont* font);

#endif
