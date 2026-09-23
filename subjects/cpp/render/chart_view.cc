#include "render/chart_view.h"

#include "render/cairo_text.h"
#include "render/chart_scale.h"

#include <algorithm>
#include <cstdio>
#include <map>
#include <cmath>
#include <numbers>
#include <sstream>

namespace {

// Pango absolute size uses device pixels here; 19px is about 14.25pt at 96dpi.
constexpr double kChartMinimumTextSize = 19;

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
        draw_cairo_text(
            cr,
            label,
            frame.left - 8,
            y,
            kChartMinimumTextSize,
            kChartMutedText,
            false,
            1.0);
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
            cr->arc(cx, cy, radius, 0, 2 * std::numbers::pi);
            cr->stroke();

            if (total > 0) {
                double angle = -std::numbers::pi / 2;
                const auto draw_segment =
                    [&](double value, const ChartColor& color) {
                        if (value <= 0) {
                            return;
                        }
                        const double sweep = (value / total) * 2 * std::numbers::pi;
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
            draw_cairo_text(
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
    area->set_content_height(240);
    area->set_hexpand(true);
    area->set_draw_func(
        [histogram](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            const int peak = *max_element(histogram.begin(), histogram.end());
            const ChartFrame frame = make_frame(width, height, 52, 36);
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
                    draw_cairo_text(
                        cr,
                        to_string(static_cast<long>(value)),
                        geometry.x + geometry.width / 2,
                        frame.bottom - bar_height - 13,
                        kChartMinimumTextSize,
                        kChartMutedText,
                        true,
                        0.5);
                }

                draw_cairo_text(
                    cr,
                    to_string(level) + " 星",
                    geometry.x + geometry.width / 2,
                    frame.bottom + 17,
                    kChartMinimumTextSize,
                    kChartMutedText,
                    false,
                    0.5);
            }
        });
    return area;
}

namespace {

// 章节配色：同一章的知识点同色，相邻章换色。颜色在这张图里只表示"属于
// 哪一章"，掌握程度由柱高表达——一个通道一个维度（AGENTS.md）。
const ChartColor& chapter_color(size_t index) {
    static const ChartColor palette[] = {
        {0.039, 0.345, 0.792},  // primary
        {0.125, 0.788, 0.592},  // teal
        {0.992, 0.494, 0.078},  // orange
        {0.435, 0.259, 0.757},  // purple
        {0.098, 0.529, 0.329},  // success
        {0.863, 0.208, 0.271},  // danger
    };
    return palette[index % (sizeof(palette) / sizeof(palette[0]))];
}

ChartColor lighten(const ChartColor& color, double amount) {
    return ChartColor{
        color.r + (1.0 - color.r) * amount,
        color.g + (1.0 - color.g) * amount,
        color.b + (1.0 - color.b) * amount,
    };
}

} // namespace

string circled_index(size_t one_based) {
    static const char* circled[] = {
        "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
        "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳",
    };
    constexpr size_t count = sizeof(circled) / sizeof(circled[0]);
    return one_based >= 1 && one_based <= count ? circled[one_based - 1]
                                                : to_string(one_based);
}

string chapter_palette_hex(size_t chapter_index) {
    const ChartColor& color = chapter_color(chapter_index);
    char buffer[8];
    snprintf(
        buffer, sizeof(buffer), "#%02x%02x%02x",
        static_cast<int>(color.r * 255 + 0.5),
        static_cast<int>(color.g * 255 + 0.5),
        static_cast<int>(color.b * 255 + 0.5));
    return buffer;
}

Gtk::DrawingArea* make_mastery_by_point_chart(const vector<MasteryPoint>& points) {
    auto area = Gtk::make_managed<Gtk::DrawingArea>();
    // 横轴只画带圈序号，知识点名在图外的对照表里，所以底部不必留竖排
    // 标签的空间。
    area->set_content_height(300);
    area->set_hexpand(true);
    area->set_draw_func(
        [points](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            if (points.empty()) {
                return;
            }
            // 纵轴固定 0-5：熟练度的量程是确定的，按数据缩放反而会让
            // "都才 1 星"看起来像已经过半。
            // 不走 make_frame：它的顶部留白固定 10px，放不下横排的章节名
            // （那一行同时充当图例）。这里手工给顶部留 36px。
            const ChartFrame frame{
                52.0, 36.0, static_cast<double>(width) - 8.0,
                static_cast<double>(height) - 40.0};
            if (frame.width() <= 0 || frame.height() <= 0) {
                return;
            }
            const vector<double> ticks = {0, 1, 2, 3, 4, 5};
            draw_value_axis(cr, frame, ticks, kMaxMastery, false);

            // 章节按首次出现的顺序分配颜色。
            map<string, size_t> color_index;
            for (const auto& point : points) {
                color_index.emplace(point.chapter_title, color_index.size());
            }

            string previous_chapter;
            for (size_t index = 0; index < points.size(); ++index) {
                const auto& point = points[index];
                const auto geometry = bar_geometry(frame, points.size(), index);
                const double value = clamp(point.mastery, 0, kMaxMastery);
                const double bar_height = frame.height() * (value / kMaxMastery);

                const ChartColor color =
                    chapter_color(color_index.at(point.chapter_title));
                if (value > 0) {
                    cr->set_source_rgb(color.r, color.g, color.b);
                    cr->rectangle(
                        geometry.x, frame.bottom - bar_height, geometry.width,
                        bar_height);
                    cr->fill();
                    // 满格柱子顶到绘图区上沿，数字再画在柱子上方就会被裁掉
                    // （看起来像个横杠）。放不下时改画在柱子内部。
                    const double above = frame.bottom - bar_height - 13;
                    const bool fits_above = above >= frame.top + 10;
                    draw_cairo_text(
                        cr, to_string(static_cast<long>(value)),
                        geometry.x + geometry.width / 2,
                        fits_above ? above : frame.bottom - bar_height + 18,
                        kChartMinimumTextSize,
                        fits_above ? kChartMutedText : ChartColor{1.0, 1.0, 1.0},
                        true, 0.5);
                } else {
                    // 未开始画一条空槽：完全不画会让人以为图没渲染出来。
                    // 用本章颜色的淡版，分组仍然看得出来。
                    const ChartColor faded = lighten(color, 0.82);
                    cr->set_source_rgb(faded.r, faded.g, faded.b);
                    cr->rectangle(geometry.x, frame.bottom - 4, geometry.width, 4);
                    cr->fill();
                }

                // 横轴只写序号，对应关系放在图外的对照表里：序号只占一个字
                // 宽，柱子再密也不会重叠，也就不必纠结竖排该往哪个方向读。
                draw_cairo_text(
                    cr, circled_index(index + 1),
                    geometry.x + geometry.width / 2, frame.bottom + 18,
                    kChartMinimumTextSize, color, true, 0.5);

                // 章节名横排在图顶，标出这一段属于哪一章；放底下会和竖排的
                // 知识点名抢位置。
                if (point.chapter_title != previous_chapter) {
                    previous_chapter = point.chapter_title;
                    // 章节名用本章配色，顶部这一行就是图例，不必另开一块。
                    draw_cairo_text(
                        cr, point.chapter_title, geometry.x, frame.top - 14,
                        kChartMinimumTextSize,
                        chapter_color(color_index.at(point.chapter_title)),
                        true, 0.0);
                    if (index > 0) {
                        cr->set_source_rgb(0.87, 0.89, 0.91);
                        cr->set_line_width(1.0);
                        cr->move_to(geometry.x - 6, frame.top - 6);
                        cr->line_to(geometry.x - 6, frame.bottom + 26);
                        cr->stroke();
                    }
                }
            }
        });
    return area;
}
