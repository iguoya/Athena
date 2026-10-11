#include "render/cairo_shapes.h"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <vector>

using namespace std;

namespace shapes {

void rounded_box(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double x,
    double y,
    double width,
    double height,
    const ChartColor& border,
    const ChartColor& fill,
    bool dashed) {
    const double radius = 8.0;
    cr->begin_new_sub_path();
    cr->arc(x + width - radius, y + radius, radius, -std::numbers::pi / 2, 0);
    cr->arc(x + width - radius, y + height - radius, radius, 0, std::numbers::pi / 2);
    cr->arc(x + radius, y + height - radius, radius, std::numbers::pi / 2, std::numbers::pi);
    cr->arc(x + radius, y + radius, radius, std::numbers::pi, 3 * std::numbers::pi / 2);
    cr->close_path();
    cr->set_source_rgb(fill.r, fill.g, fill.b);
    cr->fill_preserve();
    cr->set_source_rgb(border.r, border.g, border.b);
    cr->set_line_width(1.6);
    if (dashed) {
        cr->set_dash(vector<double>{4.0, 3.0}, 0.0);
    } else {
        cr->unset_dash();
    }
    cr->stroke();
    cr->unset_dash();
}

void arrow(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double from_x,
    double from_y,
    double to_x,
    double to_y,
    const ChartColor& color,
    bool dashed,
    double line_width) {
    cr->set_source_rgb(color.r, color.g, color.b);
    cr->set_line_width(line_width);
    if (dashed) {
        cr->set_dash(vector<double>{4.0, 3.0}, 0.0);
    } else {
        cr->unset_dash();
    }
    cr->move_to(from_x, from_y);
    cr->line_to(to_x, to_y);
    cr->stroke();
    cr->unset_dash();

    const double angle = atan2(to_y - from_y, to_x - from_x);
    const double head = 8.0;
    cr->move_to(to_x, to_y);
    cr->line_to(
        to_x - head * cos(angle - 0.42), to_y - head * sin(angle - 0.42));
    cr->line_to(
        to_x - head * cos(angle + 0.42), to_y - head * sin(angle + 0.42));
    cr->close_path();
    cr->fill();
}

void diamond(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double center_x,
    double center_y,
    double half_width,
    double half_height,
    const ChartColor& border,
    const ChartColor& fill) {
    cr->move_to(center_x, center_y - half_height);
    cr->line_to(center_x + half_width, center_y);
    cr->line_to(center_x, center_y + half_height);
    cr->line_to(center_x - half_width, center_y);
    cr->close_path();
    cr->set_source_rgb(fill.r, fill.g, fill.b);
    cr->fill_preserve();
    cr->set_source_rgb(border.r, border.g, border.b);
    cr->set_line_width(1.6);
    cr->stroke();
}

double begin_design_space(
    const Cairo::RefPtr<Cairo::Context>& cr,
    int width,
    int height,
    double design_width,
    double design_height,
    double max_scale) {
    const double scale = clamp(
        min(width / design_width, height / design_height), 1.0, max_scale);
    cr->save();
    cr->translate((width - design_width * scale) / 2.0, 0.0);
    cr->scale(scale, scale);
    return scale;
}

} // namespace shapes
