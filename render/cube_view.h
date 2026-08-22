#pragma once

#include <gtkmm.h>

using namespace std;

// 2 阶魔方的等距（isometric）示意图：只画三个可见面（上/左/右），
// 每个面按 2x2 贴纸格细分——2 阶魔方只有 8 个角块，没有棱块和中心块，
// 每个可见面正好是 2x2，不用像 3 阶那样再区分棱块/中心块的渲染。
//
// 现在只是固定配色的占位图，没有跟真实魔方状态联动：状态表示方案
// （怎么描述 8 个角块的位置和朝向）还没定，等定下来后再把这里改成
// 接收真实状态、按角块贴纸颜色渲染。跟 render/chart_view.h 一样用
// Cairo 直接手绘，不引入图表/3D 库。
Gtk::DrawingArea* make_cube_isometric_view();
