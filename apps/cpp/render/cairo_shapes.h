#pragma once

#include "render/chart_scale.h"

#include <cairomm/context.h>

using namespace std;

// Cairo 自绘视图共用的几何图元。原本各视图各写一份圆角框和箭头，ADR 0038
// 把插图也迁到自绘之后重复更明显，因此提到这里。
//
// 这里只放"怎么画一个形状"，不放任何布局或配色决策——那些属于各自的视图。
namespace shapes {

// 圆角矩形：先填充后描边，dashed 用于表达"这一格不成立"这类虚指。
void rounded_box(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double x,
    double y,
    double width,
    double height,
    const ChartColor& border,
    const ChartColor& fill,
    bool dashed = false);

// 带箭头的直线。dashed 表示"只是另一个名字"这类非实体连接。
void arrow(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double from_x,
    double from_y,
    double to_x,
    double to_y,
    const ChartColor& color,
    bool dashed = false,
    double line_width = 1.8);

// 菱形判断节点，用于流程图。
void diamond(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double center_x,
    double center_y,
    double half_width,
    double half_height,
    const ChartColor& border,
    const ChartColor& fill);

// 把画布切换到固定的设计坐标系：内容按 design_width × design_height 绘制，
// 这里负责等比放大并水平居中，调用方画完后 cr->restore()。
// 返回实际用到的缩放倍数，便于调用方在需要时微调。
//
// 为什么要这一层：自绘图如果直接用画布像素坐标，窗口一宽图形就散开、一窄
// 就重叠；固定设计坐标之后，几何与字号一起缩放，在 4K 和笔记本上都成比例。
double begin_design_space(
    const Cairo::RefPtr<Cairo::Context>& cr,
    int width,
    int height,
    double design_width,
    double design_height,
    double max_scale = 1.9);

} // namespace shapes
