#include "cjk_font.h"

// lv_font_conv 生成的子集字体（界面全部汉字 + ASCII）。
extern const lv_font_t font_cn_20;
extern const lv_font_t font_cn_28;

CjkFont cjk_font_load(void) {
    CjkFont font = {
        .body = &font_cn_20,
        .title = &font_cn_28,
        .path = "simhei.ttf via lv_font_conv（预生成子集）",
    };
    return font;
}

void cjk_font_free(CjkFont* font) {
    font->body = NULL;
    font->title = NULL;
    font->path = NULL;
}
