#include "render/cube_view.h"

#include "render/chart_scale.h"

#include <cmath>

namespace {

struct IsoPoint {
    double x = 0;
    double y = 0;
};

// origin 是立方体最靠前、三个可见面共享的那个角点；(u, v) 是沿
// dir_u/dir_v 两个方向、以“边长”为单位的坐标，u=v=0 落在 origin。
IsoPoint iso_point(
    const IsoPoint& origin,
    const IsoPoint& dir_u,
    const IsoPoint& dir_v,
    double edge,
    double u,
    double v) {
    return {
        origin.x + (dir_u.x * u + dir_v.x * v) * edge,
        origin.y + (dir_u.y * u + dir_v.y * v) * edge,
    };
}

// 画一个可见面的 2x2 贴纸格；格与格之间的描边就是分隔线，不用另外画
// 网格。面本身由 origin 沿 dir_u、dir_v 两个方向展开成 edge x edge
// 的平行四边形（顶面是菱形，侧面是斜的矩形，取决于两个方向向量）。
void draw_cube_face(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const IsoPoint& origin,
    const IsoPoint& dir_u,
    const IsoPoint& dir_v,
    double edge,
    const ChartColor& color) {
    for (int ui = 0; ui < 2; ++ui) {
        for (int vi = 0; vi < 2; ++vi) {
            const double u0 = ui * 0.5;
            const double v0 = vi * 0.5;
            const auto p00 = iso_point(origin, dir_u, dir_v, edge, u0, v0);
            const auto p10 = iso_point(origin, dir_u, dir_v, edge, u0 + 0.5, v0);
            const auto p11 =
                iso_point(origin, dir_u, dir_v, edge, u0 + 0.5, v0 + 0.5);
            const auto p01 = iso_point(origin, dir_u, dir_v, edge, u0, v0 + 0.5);
            cr->move_to(p00.x, p00.y);
            cr->line_to(p10.x, p10.y);
            cr->line_to(p11.x, p11.y);
            cr->line_to(p01.x, p01.y);
            cr->close_path();
            cr->set_source_rgb(color.r, color.g, color.b);
            cr->fill_preserve();
            cr->set_source_rgba(0, 0, 0, 0.35);
            cr->set_line_width(1.6);
            cr->stroke();
        }
    }
}

} // namespace

Gtk::DrawingArea* make_cube_isometric_view() {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(240);
    area->set_content_height(240);
    area->set_draw_func(
        [](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const double edge = min(width, height) * 0.42;
            constexpr double angle = M_PI / 6;  // 30°，标准等距投影角。
            const IsoPoint dir_right{cos(angle), -sin(angle)};
            const IsoPoint dir_left{-cos(angle), -sin(angle)};
            const IsoPoint dir_down{0, 1};
            // origin 稍微上移，给顶面和两个侧面留出对称的上下边距。
            const IsoPoint origin{width / 2.0, height / 2.0 - edge * 0.25};

            // 占位配色，贴近真实魔方：上=白，左=橙，右=绿。三个面都以
            // origin 为公共角，分别沿 (右,左)/(左,下)/(右,下) 两个方向
            // 展开，正好在 origin 处严丝合缝拼成一个立方体。
            draw_cube_face(
                cr, origin, dir_right, dir_left, edge, chart_color(0xf5f5f5));
            draw_cube_face(
                cr, origin, dir_left, dir_down, edge, chart_color(0xfd7e14));
            draw_cube_face(
                cr, origin, dir_right, dir_down, edge, chart_color(0x198754));
        });
    return area;
}
