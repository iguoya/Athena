#pragma once

#include "registry/chapter_catalog.h"

#include <gtkmm.h>

void configure_icon_image(Gtk::Image& image, const IconSpec& icon, int pixel_size);
Gtk::Image* make_icon_image(const IconSpec& icon, int pixel_size);

// 星级（知识点难度、熟练度）全应用只有这一种画法：固定 kStarCount 颗 GTK
// symbolic 星，亮的用 starred-symbolic、暗的用 non-starred-symbolic，颜色由外面
// 的 CSS `color` 决定（symbolic 图标跟着 color 着色）。不用文字 ★☆：它跟着字体走，
// 大小、基线、着色方式都和图标对不上，同一个星级会长成两个样子。
constexpr int kStarCount = 5;
Gtk::Box* make_star_row(int filled, int pixel_size, int spacing);
// 熟练度会随自测刷新：只改亮几颗，不重建控件。
void set_star_row(Gtk::Box& row, int filled);
