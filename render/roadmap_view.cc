#include "roadmap_view.h"

#include "render/cairo_text.h"
#include "render/chart_scale.h"

#include <algorithm>
#include <cmath>
#include <utility>

using namespace std;

namespace {

constexpr ChartColor kInk{0.129, 0.145, 0.161};   // #212529
constexpr ChartColor kMuted{0.424, 0.459, 0.490}; // #6c757d

void rounded_box(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double x,
    double y,
    double width,
    double height,
    const ChartColor& border,
    const ChartColor& fill) {
    const double radius = 8.0;
    cr->begin_new_sub_path();
    cr->arc(x + width - radius, y + radius, radius, -M_PI / 2, 0);
    cr->arc(x + width - radius, y + height - radius, radius, 0, M_PI / 2);
    cr->arc(x + radius, y + height - radius, radius, M_PI / 2, M_PI);
    cr->arc(x + radius, y + radius, radius, M_PI, 1.5 * M_PI);
    cr->close_path();
    cr->set_source_rgb(fill.r, fill.g, fill.b);
    cr->fill_preserve();
    cr->set_source_rgb(border.r, border.g, border.b);
    cr->set_line_width(1.6);
    cr->stroke();
}

// 与 .badge-difficulty.difficulty-level-N 同一套色阶：徽章和图上对同一个
// 难度用同一个颜色，读者不必在两套编码之间换算。
pair<ChartColor, ChartColor> difficulty_colors(int difficulty) {
    switch (difficulty) {
    case 1:
        return {{0.098, 0.529, 0.329}, {0.847, 0.937, 0.890}};  // success
    case 2:
        return {{0.125, 0.788, 0.592}, {0.878, 0.973, 0.949}};  // teal
    case 3:
        return {{0.808, 0.612, 0.024}, {1.0, 0.953, 0.808}};    // warning
    case 4:
        return {{0.992, 0.494, 0.078}, {0.996, 0.914, 0.843}};  // orange
    case 5:
        return {{0.863, 0.208, 0.271}, {0.973, 0.843, 0.855}};  // danger
    default:
        return {kMuted, {0.97, 0.98, 0.99}};
    }
}

pair<ChartColor, ChartColor> goal_colors(MasteryGoal goal) {
    switch (goal) {
    case MasteryGoal::Master:
        return {{0.039, 0.345, 0.792}, {0.878, 0.925, 1.0}};
    case MasteryGoal::Required:
        return {{0.125, 0.788, 0.592}, {0.878, 0.973, 0.949}};
    case MasteryGoal::Familiar:
    case MasteryGoal::Unrated:
        break;
    }
    return {kMuted, {0.97, 0.98, 0.99}};
}

const char* goal_text(MasteryGoal goal) {
    switch (goal) {
    case MasteryGoal::Master:
        return "需要精通";
    case MasteryGoal::Required:
        return "必须掌握";
    case MasteryGoal::Familiar:
        return "一般了解";
    case MasteryGoal::Unrated:
        break;
    }
    return "未评定";
}

} // namespace

RoadmapView::RoadmapView(
    const ChapterMeta& chapter,
    Options options,
    function<void(const string&)> on_open)
    : m_chapter(chapter),
      m_options(options),
      m_on_open(std::move(on_open)) {
    m_area = Gtk::make_managed<Gtk::DrawingArea>();
    m_area->set_hexpand(true);
    m_area->set_draw_func(
        [this](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw(cr, width, height);
        });
    auto click = Gtk::GestureClick::create();
    click->signal_pressed().connect(
        [this](int, double x, double y) { on_pressed(x, y); });
    m_area->add_controller(click);
    set_mastery({});
}

Gtk::Widget& RoadmapView::widget() const {
    return *m_area;
}

void RoadmapView::set_mastery(const map<string, int>& mastery_by_id) {
    m_nodes.clear();
    m_edges.clear();

    // 节点顺序就是配置里的顺序，而配置顺序已经是 requires 的拓扑序
    // （推荐学习顺序），所以从左上到右下读就是推荐路径。
    for (const auto& subchapter : m_chapter.subchapters) {
        const auto found = mastery_by_id.find(subchapter.function_id);
        m_nodes.push_back(Node{
            .name = subchapter.name,
            .title = subchapter.title,
            .goal = subchapter.mastery_goal,
            .difficulty = subchapter.difficulty,
            .mastery = found == mastery_by_id.end() ? 0 : found->second,
        });
    }

    for (size_t i = 0; i < m_chapter.subchapters.size(); ++i) {
        for (const auto& requirement : m_chapter.subchapters[i].requires_points) {
            // 跨章先修不画：这张图只讲本章内部的顺序。
            if (!requirement.same_chapter) {
                continue;
            }
            for (size_t j = 0; j < m_chapter.subchapters.size(); ++j) {
                if (m_chapter.subchapters[j].function_id
                    == requirement.function_id) {
                    m_edges.emplace_back(j, i);
                    break;
                }
            }
        }
    }
    if (m_area) {
        m_area->queue_draw();
    }
}

void RoadmapView::draw(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int) {
    if (m_nodes.empty()) {
        return;
    }

    // 三列纵向排布：读起来是一条从上到下的推荐路径，同时留出足够横向空间
    // 让先修连线不互相压住。
    constexpr double kNodeWidth = 190.0;
    const double node_height = m_options.show_goal_text ? 78.0 : 62.0;
    constexpr double kRowGap = 34.0;
    const double columns = 3.0;
    const double usable = static_cast<double>(width) - 24.0;
    const double column_step = max(kNodeWidth + 20.0, usable / columns);
    const double left = 12.0 + (usable - column_step * columns) / 2.0;

    for (size_t i = 0; i < m_nodes.size(); ++i) {
        const double column = static_cast<double>(i % 3);
        const double row = static_cast<double>(i / 3);
        auto& node = m_nodes[i];
        node.width = kNodeWidth;
        node.height = node_height;
        node.x = left + column * column_step + (column_step - kNodeWidth) / 2.0;
        node.y = 16.0 + row * (node_height + kRowGap);
    }

    // 先画连线，节点压在上面。
    for (const auto& [from, to] : m_edges) {
        const auto& a = m_nodes[from];
        const auto& b = m_nodes[to];
        const double x1 = a.x + a.width / 2.0;
        const double y1 = a.y + a.height;
        const double x2 = b.x + b.width / 2.0;
        const double y2 = b.y;

        cr->set_source_rgb(kMuted.r, kMuted.g, kMuted.b);
        cr->set_line_width(1.4);
        cr->move_to(x1, y1);
        // 同一行内的依赖走直线，跨行的走一段折线，避免斜穿其它节点。
        if (abs(y2 - y1) < 4.0) {
            cr->line_to(x2, y2);
        } else {
            const double middle = (y1 + y2) / 2.0;
            cr->curve_to(x1, middle, x2, middle, x2, y2);
        }
        cr->stroke();

        const double angle = atan2(y2 - (y1 + y2) / 2.0, x2 - x1);
        cr->move_to(x2, y2);
        cr->line_to(x2 - 6.0 * cos(angle - 0.5), y2 - 6.0 * sin(angle - 0.5));
        cr->line_to(x2 - 6.0 * cos(angle + 0.5), y2 - 6.0 * sin(angle + 0.5));
        cr->close_path();
        cr->fill();
    }

    for (const auto& node : m_nodes) {
        const auto [border, fill] =
            m_options.color_by == ColorBy::Difficulty
                ? difficulty_colors(node.difficulty)
                : goal_colors(node.goal);
        rounded_box(cr, node.x, node.y, node.width, node.height, border, fill);
        draw_cairo_text(
            cr, node.title, node.x + node.width / 2.0, node.y + 24.0, 14.0, kInk,
            true, 0.5);

        if (m_options.show_goal_text) {
            draw_cairo_text(
                cr, goal_text(node.goal), node.x + node.width / 2.0,
                node.y + 46.0, 11.0, kMuted, false, 0.5);
        }

        if (!m_options.show_progress) {
            continue;
        }
        // 底部细条：当前熟练度。没有记录时留空槽，一眼看出哪几节还没开始。
        const double track_x = node.x + 14.0;
        const double track_w = node.width - 28.0;
        const double track_y = node.y + node.height - 16.0;
        cr->set_source_rgb(0.87, 0.89, 0.91);
        cr->rectangle(track_x, track_y, track_w, 5.0);
        cr->fill();
        if (node.mastery > 0) {
            cr->set_source_rgb(border.r, border.g, border.b);
            cr->rectangle(
                track_x, track_y, track_w * clamp(node.mastery, 0, 5) / 5.0, 5.0);
            cr->fill();
        }
    }
}

void RoadmapView::on_pressed(double x, double y) {
    if (!m_on_open) {
        return;
    }
    for (const auto& node : m_nodes) {
        if (x < node.x || x > node.x + node.width || y < node.y
            || y > node.y + node.height) {
            continue;
        }
        m_on_open(node.name);
        return;
    }
}
