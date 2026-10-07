/* LVGL 样式橱窗：展示嵌入式出身的外观引擎在桌面上的「手机级」观感。
 *
 * 演示三层能力：样式属性（圆角/渐变/间距逐项设置）、内置主题（亮暗一键切换）、
 * 动画系统（lv_anim 驱动的呼吸与数据流动）。GTK 讲声明式、ImGui 讲参数化，
 * LVGL 的路线是「属性即布局的一部分」。
 *
 * 文本用英文：内置 Montserrat 不含 CJK，tiny_ttf 有 CJK 死锁缺陷（见 lv_conf.h）。
 */

#include "lvgl.h"
#define SDL_MAIN_HANDLED /* 我们自己写 main，不要 SDL_main.h 的劫持 */
#include <SDL.h>
#include <math.h>
#include <stdio.h>

static lv_obj_t *arc_label;
static lv_obj_t *chart;
static lv_chart_series_t *ser;
static lv_obj_t *breath_card;
static lv_obj_t *root_page;
static lv_timer_t *data_timer; /* 只删这一个；全局 timer 链里还有 SDL 事件泵 */

/* ---------- 各卡片 ---------- */

static lv_obj_t *
make_card(lv_obj_t *parent, const char *title)
{
  lv_obj_t *card = lv_obj_create(parent);
  lv_obj_set_size(card, 290, 250);
  lv_obj_set_style_radius(card, 18, 0);
  lv_obj_set_style_pad_all(card, 16, 0);
  lv_obj_set_style_border_width(card, 0, 0);
  lv_obj_set_scrollbar_mode(card, LV_SCROLLBAR_MODE_OFF);

  lv_obj_t *label = lv_label_create(card);
  lv_label_set_text(label, title);
  lv_obj_set_style_text_font(label, &lv_font_montserrat_16, 0);
  lv_obj_align(label, LV_ALIGN_TOP_LEFT, 0, 0);
  return card;
}

static void
arc_card(lv_obj_t *parent)
{
  lv_obj_t *card = make_card(parent, "Gauge: Arc");
  lv_obj_t *arc = lv_arc_create(card);
  lv_obj_set_size(arc, 150, 150);
  lv_obj_align(arc, LV_ALIGN_BOTTOM_MID, 0, -4);
  lv_arc_set_rotation(arc, 135);
  lv_arc_set_bg_angles(arc, 0, 270);
  lv_arc_set_range(arc, 0, 100);
  lv_arc_set_value(arc, 62);
  lv_obj_remove_style(arc, NULL, LV_PART_KNOB);   /* 去旋钮，纯指示 */
  lv_obj_clear_flag(arc, LV_OBJ_FLAG_CLICKABLE);
  lv_obj_set_style_arc_color(arc, lv_palette_main(LV_PALETTE_GREEN), LV_PART_INDICATOR);
  lv_obj_set_style_arc_width(arc, 14, LV_PART_INDICATOR);
  lv_obj_set_style_arc_width(arc, 14, LV_PART_MAIN);
  lv_obj_set_style_arc_opa(arc, LV_OPA_30, LV_PART_MAIN);

  arc_label = lv_label_create(arc);
  lv_obj_set_style_text_font(arc_label, &lv_font_montserrat_28, 0);
  lv_label_set_text(arc_label, "62%");
  lv_obj_center(arc_label);
}

static void
controls_card(lv_obj_t *parent)
{
  lv_obj_t *card = make_card(parent, "Controls: Slider & Switch");
  lv_obj_set_scroll_dir(card, LV_DIR_VER);

  lv_obj_t *slider = lv_slider_create(card);
  lv_obj_set_width(slider, 230);
  lv_obj_align(slider, LV_ALIGN_TOP_MID, 0, 40);
  lv_slider_set_value(slider, 64, LV_ANIM_ON);
  /* 渐变指示条 + 圆形把手：LVGL 的样式属性逐项可调 */
  lv_obj_set_style_bg_color(slider, lv_palette_lighten(LV_PALETTE_GREY, 2), LV_PART_MAIN);
  lv_obj_set_style_bg_grad_color(slider, lv_palette_main(LV_PALETTE_BLUE), LV_PART_INDICATOR);
  lv_obj_set_style_bg_grad_dir(slider, LV_GRAD_DIR_HOR, LV_PART_INDICATOR);
  lv_obj_set_style_pad_all(slider, 6, LV_PART_KNOB);

  lv_obj_t *sw = lv_switch_create(card);
  lv_obj_align(sw, LV_ALIGN_TOP_MID, 0, 110);
  lv_obj_set_style_bg_color(sw, lv_palette_main(LV_PALETTE_GREEN), LV_PART_INDICATOR | LV_STATE_CHECKED);
  lv_obj_set_size(sw, 64, 34);

  lv_obj_t *cb = lv_checkbox_create(card);
  lv_checkbox_set_text(cb, "Auto sync");
  lv_obj_align(cb, LV_ALIGN_TOP_MID, 0, 165);
}

static void
chart_card(lv_obj_t *parent)
{
  lv_obj_t *card = make_card(parent, "Realtime Chart");
  chart = lv_chart_create(card);
  lv_obj_set_size(chart, 250, 170);
  lv_obj_align(chart, LV_ALIGN_BOTTOM_MID, 0, 0);
  lv_chart_set_type(chart, LV_CHART_TYPE_LINE);
  lv_chart_set_point_count(chart, 24);
  lv_chart_set_range(chart, LV_CHART_AXIS_PRIMARY_Y, 0, 100);
  lv_chart_set_update_mode(chart, LV_CHART_UPDATE_MODE_SHIFT);
  ser = lv_chart_add_series(chart, lv_palette_main(LV_PALETTE_RED), LV_CHART_AXIS_PRIMARY_Y);
  for (uint32_t i = 0; i < 24; i++)
    lv_chart_set_next_value(chart, ser, (int32_t)(50 + 40 * sinf(i * 0.5f)));
  lv_chart_refresh(chart);
}

/* ---------- 动画 ---------- */

static void
breath_cb(void *var, int32_t v)
{
  lv_obj_set_style_bg_opa(var, v, 0);
  lv_obj_set_style_shadow_opa(var, v, 0);
}

static void
make_breath_banner(lv_obj_t *parent)
{
  breath_card = lv_obj_create(parent);
  lv_obj_set_size(breath_card, LV_PCT(100), 96);
  lv_obj_set_style_radius(breath_card, 20, 0);
  lv_obj_set_style_border_width(breath_card, 0, 0);
  lv_obj_set_style_pad_all(breath_card, 20, 0);
  lv_obj_set_scrollbar_mode(breath_card, LV_SCROLLBAR_MODE_OFF);
  /* 渐变横幅：与 GTK 的 .hero 同一思路，只是写法是属性而非样式表 */
  lv_obj_set_style_bg_color(breath_card, lv_palette_darken(LV_PALETTE_INDIGO, 2), 0);
  lv_obj_set_style_bg_grad_color(breath_card, lv_palette_main(LV_PALETTE_PURPLE), 0);
  lv_obj_set_style_bg_grad_dir(breath_card, LV_GRAD_DIR_HOR, 0);
  lv_obj_set_style_bg_opa(breath_card, LV_OPA_COVER, 0);
  lv_obj_set_style_shadow_width(breath_card, 60, 0);
  lv_obj_set_style_shadow_color(breath_card, lv_palette_main(LV_PALETTE_PURPLE), 0);

  lv_obj_t *title = lv_label_create(breath_card);
  lv_label_set_text(title, "Animation-driven look");
  lv_obj_set_style_text_font(title, &lv_font_montserrat_28, 0);
  lv_obj_set_style_text_color(title, lv_color_white(), 0);
  lv_obj_align(title, LV_ALIGN_LEFT_MID, 0, 0);

  lv_obj_t *sub = lv_label_create(breath_card);
  lv_label_set_text(sub, "lv_anim breathes opacity & glow - style is the UI");
  lv_obj_set_style_text_color(sub, lv_color_hex(0xE0D7FF), 0);
  lv_obj_align(sub, LV_ALIGN_LEFT_MID, 0, 34);

  lv_anim_t a;
  lv_anim_init(&a);
  lv_anim_set_var(&a, breath_card);
  lv_anim_set_exec_cb(&a, breath_cb);
  lv_anim_set_values(&a, LV_OPA_70, LV_OPA_COVER);
  lv_anim_set_time(&a, 1400);
  lv_anim_set_playback_time(&a, 1400);
  lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE);
  lv_anim_start(&a);
}

/* ---------- 定时器：数据流动 ---------- */

static void
tick_timer_cb(lv_timer_t *timer)
{
  (void)timer;
  static uint32_t n = 0;
  n++;
  int32_t v = (int32_t)(50 + 38 * sinf(n * 0.35f) + (rand() % 10));
  lv_chart_set_next_value(chart, ser, v);

  int32_t arc_v = (int32_t)(50 + 45 * sinf(n * 0.12f));
  lv_arc_set_value(lv_obj_get_child(
                       lv_obj_get_parent(arc_label), 0),
                   arc_v);
  lv_label_set_text_fmt(arc_label, "%d%%", arc_v);
}

/* ---------- 页面与主题 ---------- */

static void
build_page(void)
{
  root_page = lv_obj_create(lv_screen_active());
  lv_obj_set_size(root_page, LV_PCT(100), LV_PCT(100));
  lv_obj_set_style_pad_all(root_page, 22, 0);
  lv_obj_set_style_pad_row(root_page, 18, 0);
  lv_obj_set_style_pad_column(root_page, 18, 0);
  lv_obj_set_flex_flow(root_page, LV_FLEX_FLOW_COLUMN);
  lv_obj_set_scrollbar_mode(root_page, LV_SCROLLBAR_MODE_OFF);
  lv_obj_set_style_border_width(root_page, 0, 0);

  make_breath_banner(root_page);

  lv_obj_t *row = lv_obj_create(root_page);
  lv_obj_set_size(row, LV_PCT(100), LV_SIZE_CONTENT);
  lv_obj_set_style_pad_all(row, 0, 0);
  lv_obj_set_style_pad_column(row, 18, 0);
  lv_obj_set_style_border_width(row, 0, 0);
  lv_obj_set_flex_flow(row, LV_FLEX_FLOW_ROW);
  lv_obj_set_scrollbar_mode(row, LV_SCROLLBAR_MODE_OFF);

  arc_card(row);
  controls_card(row);
  chart_card(row);

  data_timer = lv_timer_create(tick_timer_cb, 120, NULL);
}

static void
on_theme_toggle(lv_event_t *e)
{
  (void)e;
  static bool dark = true;
  dark = !dark;
  /* 重新初始化默认主题并重建页面：亮暗一键切换 */
  lv_theme_default_init(lv_display_get_default(),
                        lv_palette_main(LV_PALETTE_BLUE),
                        lv_palette_main(LV_PALETTE_RED),
                        dark, LV_FONT_DEFAULT);
  if (data_timer)
    {
      lv_timer_del(data_timer); /* 不能清全局 timer 链：SDL 事件泵也挂在上面 */
      data_timer = NULL;
    }
  lv_obj_clean(lv_screen_active());
  build_page();
}

int
main(void)
{
  lv_init();
  lv_tick_set_cb(SDL_GetTicks);

  lv_display_t *disp = lv_sdl_window_create(1000, 760);
  lv_sdl_mouse_create();

  lv_theme_default_init(disp, lv_palette_main(LV_PALETTE_BLUE),
                        lv_palette_main(LV_PALETTE_RED), true, LV_FONT_DEFAULT);
  build_page();

  /* 主题切换按钮悬浮在右上角 */
  lv_obj_t *btn = lv_button_create(lv_screen_active());
  lv_obj_align(btn, LV_ALIGN_TOP_RIGHT, -28, 26);
  lv_obj_add_event_cb(btn, on_theme_toggle, LV_EVENT_CLICKED, NULL);
  lv_obj_t *bl = lv_label_create(btn);
  lv_label_set_text(bl, "Light / Dark");

  bool running = true;
  while (running)
    {
      uint32_t next = lv_timer_handler();
      if (next > 16)
        next = 16;
      SDL_Delay(next);
    }
  return 0;
}
