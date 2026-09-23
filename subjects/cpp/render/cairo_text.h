#pragma once

#include "render/chart_scale.h"

#include <cairomm/context.h>

#include <string>

using namespace std;

// Cairo 手绘控件里统一的文本绘制。走 Pango 而不是 Cairo 的 toy text API：
// toy API 不做字体回退，在 macOS 上用 sans-serif 画"星""章"等中文会变成
// 方块；Pango 会自动挑一个可用的中文字体。
//
// x/y 是文本的锚点：align 决定水平对齐（0 左、0.5 居中、1 右），垂直方向
// 统一按视觉中心对齐，所以 y 传的是文本中线。
void draw_cairo_text(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const string& text,
    double x,
    double y,
    double size,
    const ChartColor& color,
    bool bold = false,
    double align = 0.0);
