#include "../app_window.h"
#include "../cjk_font.h"
#include "../progress.h"

#include "lvgl.h"

#include <stdio.h>

// vendor/lvgl 和 SDL2 都就位时编译这一份。LVGL 只在这个文件里出现——它是
// "让 C 能开窗口"的手段，换成别的库时其余代码一行都不用动（ADR 0032）。
//
// 界面用代码搭而不是描述文件：LVGL 没有 Blueprint 那样的布局 DSL，主程序
// 的 .blp 优先规则在这里不适用。

// 整个窗口共用一份中文字体：加载失败时退回 LVGL 内置的汉字子集，
// 那份字表偏日文与繁体，简体会缺字，但总比不显示强。
static CjkFont g_font;

static const lv_font_t* body_font(void) {
    return g_font.body != NULL ? g_font.body : &lv_font_simsun_16_cjk;
}

static const lv_font_t* title_font(void) {
    return g_font.title != NULL ? g_font.title : &lv_font_montserrat_28;
}

static lv_obj_t* make_card(lv_obj_t* parent) {
    lv_obj_t* card = lv_obj_create(parent);
    lv_obj_set_width(card, LV_PCT(100));
    lv_obj_set_height(card, LV_SIZE_CONTENT);
    lv_obj_set_style_pad_all(card, 20, 0);
    lv_obj_set_style_radius(card, 10, 0);
    lv_obj_set_flex_flow(card, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(card, 8, 0);
    return card;
}

static lv_obj_t* make_text(lv_obj_t* parent, const char* text, bool muted) {
    lv_obj_t* label = lv_label_create(parent);
    lv_label_set_text(label, text);
    lv_label_set_long_mode(label, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(label, LV_PCT(100));
    lv_obj_set_style_text_font(label, body_font(), 0);
    if (muted) {
        lv_obj_set_style_text_color(label, lv_color_hex(0x6c757d), 0);
    }
    return label;
}

static void build_ui(struct Progress* progress) {
    lv_obj_t* screen = lv_screen_active();
    lv_obj_set_style_bg_color(screen, lv_color_hex(0xf8f9fa), 0);
    lv_obj_set_flex_flow(screen, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_all(screen, 28, 0);
    lv_obj_set_style_pad_row(screen, 18, 0);

    lv_obj_t* title = lv_label_create(screen);
    lv_label_set_text(title, "Athena · C 语言编程");
    lv_obj_set_style_text_font(title, title_font(), 0);
    lv_obj_set_style_text_color(title, lv_color_hex(0x052c65), 0);

    lv_obj_t* intro = make_card(screen);
    make_text(intro, "独立学习应用已经启动。", false);
    make_text(
        intro,
        "这个窗口由 apps/c 里的独立程序自己画出来，和主程序是两个进程。"
        "它有自己的构建系统和界面技术，主程序只负责把它启动起来。",
        true);

    lv_obj_t* store = make_card(screen);
    if (progress->handle != NULL) {
        make_text(store, "学习库：已连接", false);
        const int mastery = progress_load_mastery(progress, "c.Sample.hello");
        char line[128];
        snprintf(
            line, sizeof(line),
            "和主程序共用同一个 SQLite 文件，进度记在一起。"
            "示例知识点 c.Sample.hello 当前熟练度 %d / 5。",
            mastery);
        make_text(store, line, true);
    } else {
        make_text(store, "学习库：未连接", false);
        make_text(
            store,
            "没有收到 --store 参数，或者文件不可用；这次不记录进度。",
            true);
    }

    lv_obj_t* next = make_card(screen);
    make_text(next, "下一步", false);
    make_text(
        next,
        "章节、文档和实验都放在 content/ 下自己管理，不进主程序的配置。"
        "教学规范沿用 docs/ 里那套，但格式这边自己定。",
        true);
}

int app_window_run(struct Progress* progress) {
    lv_init();

    lv_display_t* display = lv_sdl_window_create(960, 640);
    if (display == NULL) {
        fprintf(stderr, "SDL 窗口创建失败\n");
        lv_deinit();
        return 1;
    }
    lv_sdl_window_set_title(display, "Athena · C 语言编程");
    lv_sdl_mouse_create();
    lv_sdl_mousewheel_create();
    lv_sdl_keyboard_create();

    // 字体要在建界面之前准备好：控件创建时就会取字体量文字宽高。
    g_font = cjk_font_load(17, 30);
    if (g_font.path != NULL) {
        printf("中文字体：%s\n", g_font.path);
    }

    build_ui(progress);

    // 关掉窗口时 SDL 驱动会 lv_display_delete()，默认 display 随之为空，
    // 循环自然结束——LV_SDL_DIRECT_EXIT 关掉就是为了走到这里正常收尾。
    while (lv_display_get_default() != NULL) {
        const uint32_t idle = lv_timer_handler();
        lv_delay_ms(idle == LV_NO_TIMER_READY || idle > 16 ? 16 : idle);
    }

    // 字体必须在 lv_deinit 之前销毁：控件还引用着它。
    cjk_font_free(&g_font);
    lv_deinit();
    return 0;
}
