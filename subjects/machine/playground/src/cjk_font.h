#ifndef ATHENA_C_CJK_FONT_H
#define ATHENA_C_CJK_FONT_H

#include "lvgl.h"

#include <stddef.h>

// 运行时加载系统里的中文字体。
//
// LVGL 自带的 lv_font_simsun_16_cjk 不是"CJK 全集"，而是生成时用 --symbols
// 写死的约一千个字，且明显偏日文与繁体（有「應」「經」没有「应」「经」），
// 拿来显示简体中文会大面积缺字变方框。教学内容的字符集不可能提前固定，
// 所以走 tiny_ttf 运行时按需渲染字形，任何汉字都能显示。
//
// 字体文件不进仓库：各平台都自带中文字体，按候选路径找即可。

typedef struct {
    lv_font_t* body;  // 正文字号
    lv_font_t* title; // 标题字号
    void* data;       // 字体文件内容；tiny_ttf 只持有指针，必须活得比字体久
    size_t size;
    const char* path; // 实际用上的字体文件，便于排查
} CjkFont;

// 加载中文字体。找不到任何可用字体时返回的 body/title 为 NULL，
// 调用方应回退到内置字体——缺字总比不显示强。
CjkFont cjk_font_load(int body_size, int title_size);
void cjk_font_free(CjkFont* font);

#endif
