#include "cjk_font.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 候选字体按"简体黑体优先"排列。tiny_ttf 内部用
// stbtt_GetFontOffsetForIndex(data, 0) 取集合里第一个字体，所以 .ttc 也能读。
static const char* const kCandidates[] = {
    // macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    // Ubuntu / Debian
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
};

static void* read_whole_file(const char* path, size_t* out_size) {
    FILE* file = fopen(path, "rb");
    if (file == NULL) {
        return NULL;
    }
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return NULL;
    }
    const long length = ftell(file);
    if (length <= 0) {
        fclose(file);
        return NULL;
    }
    rewind(file);

    void* buffer = malloc((size_t)length);
    if (buffer == NULL) {
        fclose(file);
        return NULL;
    }
    const size_t read = fread(buffer, 1, (size_t)length, file);
    fclose(file);
    if (read != (size_t)length) {
        free(buffer);
        return NULL;
    }
    *out_size = read;
    return buffer;
}

CjkFont cjk_font_load(int body_size, int title_size) {
    CjkFont font = {0};

    // 环境变量优先，便于换字体试效果，也给候选表没覆盖到的系统留个出口。
    const char* override_path = getenv("ATHENA_C_FONT");
    const size_t candidate_count =
        sizeof(kCandidates) / sizeof(kCandidates[0]);

    for (size_t index = 0; index <= candidate_count; ++index) {
        const char* path = index == 0 ? override_path : kCandidates[index - 1];
        if (path == NULL || path[0] == '\0') {
            continue;
        }

        size_t size = 0;
        void* data = read_whole_file(path, &size);
        if (data == NULL) {
            continue;
        }

        lv_font_t* body = lv_tiny_ttf_create_data(data, size, body_size);
        if (body == NULL) {
            free(data);
            continue;
        }
        lv_font_t* title = lv_tiny_ttf_create_data(data, size, title_size);
        if (title == NULL) {
            lv_tiny_ttf_destroy(body);
            free(data);
            continue;
        }

        font.body = body;
        font.title = title;
        font.data = data;
        font.size = size;
        font.path = path;
        return font;
    }

    fprintf(stderr, "没有找到可用的中文字体，回退到内置字体（会缺字）\n");
    return font;
}

void cjk_font_free(CjkFont* font) {
    if (font->title != NULL) {
        lv_tiny_ttf_destroy(font->title);
        font->title = NULL;
    }
    if (font->body != NULL) {
        lv_tiny_ttf_destroy(font->body);
        font->body = NULL;
    }
    // 字体销毁之后才能放数据：tiny_ttf 全程只持有这块内存的指针。
    free(font->data);
    font->data = NULL;
    font->size = 0;
    font->path = NULL;
}
