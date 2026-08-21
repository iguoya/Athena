#include "render/chart_view.h"

#include "render/chart_scale.h"

#include <pangomm.h>

#include <algorithm>
#include <cmath>
#include <sstream>

namespace {

// 绘制文本统一走 Pango。Cairo 的 toy text API 不做字体回退，在 macOS 上
// 用 sans-serif 绘制“星”等中文时会变成方块；Pango 会选择可用的中文字体。
void draw_text(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const string& text,
    double x,
    double y,
    double size,
    const ChartColor& color,
    bool bold = false,
    // 水平对齐：0 左对齐，0.5 居中，1 右对齐。垂直方向统一按基线之上
    // 居中，调用方传的 y 是文本视觉中心。
    double align = 0.0) {
    auto layout = Pango::Layout::create(cr);
    Pango::FontDescription font;
    font.set_family("sans-serif");
    font.set_absolute_size(size * Pango::SCALE);
    font.set_weight(bold ? Pango::Weight::BOLD : Pango::Weight::NORMAL);
    layout->set_font_description(font);
    layout->set_text(text);
    int text_width = 0;
    int text_height = 0;
    layout->get_pixel_size(text_width, text_height);
    cr->set_source_rgb(color.r, color.g, color.b);
    cr->move_to(x - text_width * align, y - text_height / 2.0);
    layout->show_in_cairo_context(cr);
}

string format_percent(double ratio) {
    ostringstream text;
    text << lround(ratio * 100) << "%";
    return text.str();
}

// 纵轴 + 网格线的公共绘制：图表区域是 [left, top, right, bottom]，值域是
// [0, max_value]。返回值转像素的换算交给调用方，这里只画背景。
struct ChartFrame {
    double left = 0;
    double top = 0;
    double right = 0;
    double bottom = 0;

    double width() const { return right - left; }
    double height() const { return bottom - top; }
};

void draw_value_axis(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const ChartFrame& frame,
    const vector<double>& ticks,
    double axis_max,
    bool percent_labels) {
    if (axis_max <= 0) {
        return;
    }
    cr->set_line_width(1.0);
    for (const double tick : ticks) {
        const double y = frame.bottom - frame.height() * (tick / axis_max);
        // 网格线压在半像素上，避免 1px 线条被反走样糊成 2px 灰线。
        const double aligned_y = floor(y) + 0.5;
        cr->set_source_rgb(kChartAxis.r, kChartAxis.g, kChartAxis.b);
        cr->move_to(frame.left, aligned_y);
        cr->line_to(frame.right, aligned_y);
        cr->stroke();

        const string label = percent_labels
            ? format_percent(tick)
            : to_string(static_cast<long>(lround(tick)));
        draw_text(cr, label, frame.left - 6, y, 11, kChartMutedText, false, 1.0);
    }
}

// 直方图柱子的几何：把第 index 根柱子的横向范围算出来。
struct BarGeometry {
    double x = 0;
    double width = 0;
};

BarGeometry bar_geometry(const ChartFrame& frame, size_t count, size_t index) {
    constexpr double gap = 6;
    const double available = frame.width();
    const double slot = available / static_cast<double>(count);
    const double width = max(4.0, slot - gap);
    return {frame.left + slot * static_cast<double>(index) + (slot - width) / 2,
            width};
}

// 图表区域的留白：左侧留给纵轴标签，底部留给横轴标签。
ChartFrame make_frame(int width, int height, double left_margin, double bottom_margin) {
    return {left_margin, 10.0, static_cast<double>(width) - 8.0,
            static_cast<double>(height) - bottom_margin};
}

} // namespace

Gtk::Box* make_mastery_stars(int mastery) {
    auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 1);
    for (int index = 0; index < kMaxMastery; ++index) {
        auto star = Gtk::make_managed<Gtk::Label>(index < mastery ? "★" : "☆");
        star->add_css_class(
            index < mastery ? "progress-star-filled" : "progress-star-empty");
        row->append(*star);
    }
    return row;
}

Gtk::DrawingArea* make_mastery_donut_chart(
    int mastered,
    int in_progress,
    int not_started) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_width(230);
    area->set_content_height(230);
    area->set_draw_func(
        [mastered, in_progress, not_started](
            const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const double total = mastered + in_progress + not_started;
            const double cx = width / 2.0;
            const double cy = height / 2.0;
            // 先确定外沿，再把线宽的一半扣回圆心半径；旧算法只从半径
            // 扣固定 12px，却又用约 30px 的线宽，外沿会越过 DrawingArea
            // 被裁掉。18px 外边距也给高 DPI 下的抗锯齿留出余量。
            const double outer_radius = min(width, height) / 2.0 - 18;
            const double thickness = max(8.0, outer_radius * 0.32);
            const double radius = max(0.0, outer_radius - thickness / 2.0);

            cr->set_line_width(thickness);
            cr->set_line_cap(Cairo::Context::LineCap::BUTT);

            // 底环：未开始/无数据时的占位轨道。
            cr->set_source_rgba(0, 0, 0, 0.08);
            cr->arc(cx, cy, radius, 0, 2 * M_PI);
            cr->stroke();

            if (total > 0) {
                double angle = -M_PI / 2;
                const auto draw_segment =
                    [&](double value, const ChartColor& color) {
                        if (value <= 0) {
                            return;
                        }
                        const double sweep = (value / total) * 2 * M_PI;
                        cr->set_source_rgb(color.r, color.g, color.b);
                        cr->arc(cx, cy, radius, angle, angle + sweep);
                        cr->stroke();
                        angle += sweep;
                    };
                draw_segment(mastered, kChartMastered);
                draw_segment(in_progress, kChartInProgress);
                draw_segment(not_started, kChartNotStarted);
            }

            const double ratio = total > 0 ? mastered / total : 0.0;
            draw_text(
                cr, format_percent(ratio), cx, cy, 26, kChartLabelText, true, 0.5);
        });
    return area;
}

Gtk::Box* make_mastery_legend() {
    auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 14);
    row->set_halign(Gtk::Align::CENTER);
    const auto add_entry =
        [row](const string& label, const string& css_class) {
            auto entry =
                Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 5);
            auto swatch = Gtk::make_managed<Gtk::Box>();
            swatch->add_css_class("progress-legend-swatch");
            swatch->add_css_class(css_class);
            swatch->set_size_request(11, 11);
            entry->append(*swatch);
            auto text = Gtk::make_managed<Gtk::Label>(label);
            text->add_css_class("progress-chapter-count");
            entry->append(*text);
            row->append(*entry);
        };
    add_entry("已掌握", "stat-tile-mastered");
    add_entry("学习中", "stat-tile-in-progress");
    add_entry("未开始", "progress-legend-not-started");
    return row;
}

Gtk::DrawingArea* make_mastery_histogram_chart(
    const array<int, kMasteryLevels>& histogram) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    area->set_content_height(210);
    area->set_hexpand(true);
    area->set_draw_func(
        [histogram](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const int peak = *max_element(histogram.begin(), histogram.end());
            const ChartFrame frame = make_frame(width, height, 42, 26);
            if (frame.width() <= 0 || frame.height() <= 0) {
                return;
            }

            // 纵轴按实际最大值取整刻度；全 0 时 nice_ticks 会退化成 0-1，
            // 图上只剩一条基线，不会除零。
            const auto ticks = nice_ticks(0, peak, 4);
            const double axis_max = ticks.back();
            draw_value_axis(cr, frame, ticks, axis_max, false);

            for (size_t level = 0; level < histogram.size(); ++level) {
                const auto geometry =
                    bar_geometry(frame, histogram.size(), level);
                const double value = histogram[level];
                const double bar_height =
                    axis_max > 0 ? frame.height() * (value / axis_max) : 0.0;

                // 星级越高越偏绿，越低越偏橙，颜色本身也传达进度。
                const ChartColor color = mix_chart_color(
                    kChartInProgress,
                    kChartMastered,
                    static_cast<double>(level) / kMaxMastery);
                cr->set_source_rgb(color.r, color.g, color.b);
                cr->rectangle(
                    geometry.x, frame.bottom - bar_height, geometry.width, bar_height);
                cr->fill();

                if (value > 0) {
                    draw_text(
                        cr,
                        to_string(static_cast<long>(value)),
                        geometry.x + geometry.width / 2,
                        frame.bottom - bar_height - 9,
                        11,
                        kChartMutedText,
                        true,
                        0.5);
                }

                draw_text(
                    cr,
                    to_string(level) + " 星",
                    geometry.x + geometry.width / 2,
                    frame.bottom + 12,
                    11,
                    kChartMutedText,
                    false,
                    0.5);
            }
        });
    return area;
}
