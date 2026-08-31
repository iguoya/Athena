#include "render/knowledge_graph_view.h"

#include "render/chart_scale.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <string_view>

using namespace std;

namespace {

// 2K 是实际使用基线。每层按图谱真实最大并列数划分等宽轨道，节点在轨道内
// 横向铺满；高度完全交给 GTK 按完整标题、描述和指标自然测量，不设固定卡片框。
constexpr int kColumnGap = 36;
constexpr int kLayerGap = 72;

void draw_edge(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const graphene_rect_t& from,
    const graphene_rect_t& to) {
    const double x0 = from.origin.x + from.size.width / 2.0;
    const double y0 = from.origin.y + from.size.height;
    const double x1 = to.origin.x + to.size.width / 2.0;
    const double y1 = to.origin.y;
    const double midy = (y0 + y1) / 2.0;

    const ChartColor line = chart_color(0x9aa4af);
    cr->set_source_rgb(line.r, line.g, line.b);
    cr->set_line_width(2.0);
    cr->move_to(x0, y0);
    cr->curve_to(x0, midy, x1, midy, x1, y1 - 7);
    cr->stroke();

    cr->move_to(x1, y1);
    cr->line_to(x1 - 5.5, y1 - 9);
    cr->line_to(x1 + 5.5, y1 - 9);
    cr->close_path();
    cr->fill();
}

void configure_graph_icon(Gtk::Image& image, const IconSpec& icon) {
    if (icon.type == "resource" && !icon.path.empty()) {
        string path = icon.path;
        constexpr string_view prefix = "resources/";
        if (path.rfind(prefix, 0) == 0) {
            path = "/app/" + path.substr(prefix.size());
        }
        image.set_from_resource(path);
    } else if (!icon.name.empty()) {
        image.set_from_icon_name(icon.name);
    } else {
        image.set_visible(false);
    }
    image.set_pixel_size(30);
}

int completion_level(double completion) {
    return clamp(static_cast<int>(floor(completion * 5.0)), 0, 4);
}

string mastery_class(const KnowledgeNode& node) {
    if (node.total <= 0 || node.mastered == 0) {
        return "graph-mastery-none";
    }
    if (node.mastered >= node.total) {
        return "graph-mastery-all";
    }
    return "graph-mastery-some";
}

Gtk::Button* make_node_button(
    const KnowledgeNode& node,
    const function<void(const string&)>& on_open) {
    auto* button = Gtk::make_managed<Gtk::Button>();
    button->set_hexpand(true);
    button->set_halign(Gtk::Align::FILL);
    button->set_valign(Gtk::Align::FILL);
    button->add_css_class("knowledge-graph-node");
    button->add_css_class(
        "graph-importance-" + to_string(clamp(node.importance, 0, 5)));

    auto* content = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, 12);
    content->set_margin(18);

    auto* heading = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::HORIZONTAL, 9);
    auto* icon = Gtk::make_managed<Gtk::Image>();
    configure_graph_icon(*icon, node.icon);
    icon->add_css_class("knowledge-graph-node-icon");
    heading->append(*icon);

    auto* title = Gtk::make_managed<Gtk::Label>(node.title);
    title->set_halign(Gtk::Align::START);
    title->set_hexpand(true);
    title->set_xalign(0.0F);
    title->set_wrap(true);
    title->set_wrap_mode(Pango::WrapMode::WORD_CHAR);
    title->add_css_class("knowledge-graph-node-title");
    heading->append(*title);
    content->append(*heading);

    auto* description = Gtk::make_managed<Gtk::Label>(node.description);
    description->set_halign(Gtk::Align::START);
    description->set_xalign(0.0F);
    description->set_wrap(true);
    description->set_wrap_mode(Pango::WrapMode::WORD_CHAR);
    description->add_css_class("knowledge-graph-node-description");
    content->append(*description);

    auto* metrics = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::HORIZONTAL, 7);
    auto* importance = Gtk::make_managed<Gtk::Label>(
        node.importance > 0
            ? "重要度 " + to_string(node.importance) + "/5"
            : "重要度 未评");
    importance->add_css_class("graph-metric-badge");
    importance->add_css_class(
        "graph-importance-badge-" +
        to_string(clamp(node.importance, 0, 5)));
    metrics->append(*importance);

    const string mastery = node.total > 0
        ? "掌握 " + to_string(node.mastered) + "/" + to_string(node.total)
        : string("暂无知识点");
    auto* mastery_badge = Gtk::make_managed<Gtk::Label>(mastery);
    mastery_badge->add_css_class("graph-metric-badge");
    mastery_badge->add_css_class(mastery_class(node));
    metrics->append(*mastery_badge);
    content->append(*metrics);

    auto* completion = Gtk::make_managed<Gtk::ProgressBar>();
    completion->set_fraction(clamp(node.completion, 0.0, 1.0));
    completion->set_show_text(true);
    completion->set_text(
        "完成 " + to_string(static_cast<int>(lround(node.completion * 100))) +
        "%");
    completion->add_css_class("graph-completion");
    completion->add_css_class(
        "graph-completion-" + to_string(completion_level(node.completion)));
    content->append(*completion);

    button->set_child(*content);
    button->set_tooltip_text(
        node.title + "\n" + node.description + "\n章节重要度：" +
        (node.importance > 0 ? to_string(node.importance) + "/5" : "未评") +
        "\n掌握程度：" + to_string(node.mastered) + "/" +
        to_string(node.total) + "\n完成程度：" +
        to_string(static_cast<int>(lround(node.completion * 100))) + "%");
    button->signal_clicked().connect(
        [on_open, chapter_name = node.chapter_name]() {
            on_open(chapter_name);
        });
    return button;
}

Gtk::Widget* make_canvas(
    const KnowledgeGraph& graph,
    const function<void(const string&)>& on_open) {
    auto* overlay = Gtk::make_managed<Gtk::Overlay>();
    overlay->set_hexpand(true);

    const int column_count = max_element(
        graph.nodes.begin(),
        graph.nodes.end(),
        [](const KnowledgeNode& left, const KnowledgeNode& right) {
            return left.layer_size < right.layer_size;
        })->layer_size;

    auto* layers = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, kLayerGap);
    layers->set_hexpand(true);

    vector<Gtk::Button*> node_widgets(graph.nodes.size(), nullptr);
    for (int layer = 0; layer < graph.layer_count; ++layer) {
        auto* row = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, kColumnGap);
        row->set_homogeneous(true);
        row->set_hexpand(true);

        vector<int> node_at_column(static_cast<size_t>(column_count), -1);
        for (size_t index = 0; index < graph.nodes.size(); ++index) {
            const auto& node = graph.nodes[index];
            if (node.layer != layer) {
                continue;
            }
            const int column = node.layer_size == 1
                ? (column_count - 1) / 2
                : static_cast<int>(lround(
                      node.slot * (column_count - 1.0) /
                      (node.layer_size - 1.0)));
            node_at_column[static_cast<size_t>(column)] =
                static_cast<int>(index);
        }

        for (int column = 0; column < column_count; ++column) {
            const int index = node_at_column[static_cast<size_t>(column)];
            if (index < 0) {
                auto* spacer = Gtk::make_managed<Gtk::Box>();
                spacer->set_hexpand(true);
                row->append(*spacer);
                continue;
            }
            auto* button = make_node_button(
                graph.nodes[static_cast<size_t>(index)], on_open);
            node_widgets[static_cast<size_t>(index)] = button;
            row->append(*button);
        }
        layers->append(*row);
    }
    overlay->set_child(*layers);

    auto* edges = Gtk::make_managed<Gtk::DrawingArea>();
    edges->set_hexpand(true);
    edges->set_vexpand(true);
    edges->set_can_target(false);
    edges->set_draw_func(
        [graph, node_widgets, overlay](
            const Cairo::RefPtr<Cairo::Context>& cr, int, int) {
            for (const auto& edge : graph.edges) {
                graphene_rect_t from{};
                graphene_rect_t to{};
                const auto* from_widget =
                    node_widgets[static_cast<size_t>(edge.from)];
                const auto* to_widget =
                    node_widgets[static_cast<size_t>(edge.to)];
                if (from_widget && to_widget &&
                    gtk_widget_compute_bounds(
                        GTK_WIDGET(from_widget->gobj()),
                        GTK_WIDGET(overlay->gobj()),
                        &from) &&
                    gtk_widget_compute_bounds(
                        GTK_WIDGET(to_widget->gobj()),
                        GTK_WIDGET(overlay->gobj()),
                        &to)) {
                    draw_edge(cr, from, to);
                }
            }
        });
    overlay->add_overlay(*edges);
    return overlay;
}

Gtk::Box* legend_row(const string& css_class, const string& text) {
    auto* row = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::HORIZONTAL, 8);
    auto* swatch = Gtk::make_managed<Gtk::Box>();
    swatch->set_size_request(16, 16);
    swatch->add_css_class("graph-legend-swatch");
    swatch->add_css_class(css_class);
    row->append(*swatch);
    auto* label = Gtk::make_managed<Gtk::Label>(text);
    label->set_halign(Gtk::Align::START);
    label->set_xalign(0.0F);
    label->set_wrap(true);
    row->append(*label);
    return row;
}

Gtk::Widget* make_legend() {
    auto* frame = Gtk::make_managed<Gtk::Frame>("图谱说明");
    frame->add_css_class("panel-frame");
    frame->add_css_class("group-frame");
    frame->add_css_class("knowledge-graph-legend");
    frame->set_size_request(340, -1);
    frame->set_valign(Gtk::Align::START);

    auto* content = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, 10);
    content->set_margin(14);

    auto add_heading = [content](const string& text) {
        auto* label = Gtk::make_managed<Gtk::Label>(text);
        label->set_halign(Gtk::Align::START);
        label->add_css_class("heading");
        label->set_margin_top(4);
        content->append(*label);
    };
    auto add_note = [content](const string& text) {
        auto* label = Gtk::make_managed<Gtk::Label>(text);
        label->set_halign(Gtk::Align::START);
        label->set_xalign(0.0F);
        label->set_wrap(true);
        label->add_css_class("dim-label");
        label->add_css_class("knowledge-graph-legend-note");
        content->append(*label);
    };

    add_heading("连接关系");
    add_note("箭头从前置章节指向后续章节；点击节点进入对应章节。");

    add_heading("章节重要度");
    add_note("取本章所有已评知识点 importance 的平均值，四舍五入为 1–5 级。");
    auto* importance_scale = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::HORIZONTAL, 5);
    for (int level = 1; level <= 5; ++level) {
        auto* badge = Gtk::make_managed<Gtk::Label>(to_string(level));
        badge->add_css_class("graph-importance-scale");
        badge->add_css_class(
            "graph-importance-badge-" + to_string(level));
        importance_scale->append(*badge);
    }
    content->append(*importance_scale);
    add_note("冷色表示较低，暖色表示较高；灰色表示尚未评估。");

    add_heading("掌握程度");
    content->append(*legend_row("graph-mastery-none", "尚无 5 星知识点"));
    content->append(*legend_row("graph-mastery-some", "已有部分达到 5 星"));
    content->append(*legend_row("graph-mastery-all", "本章知识点全部 5 星"));

    add_heading("完成程度");
    add_note("按本章平均熟练度 ÷ 5 计算；1–4 星同样计入进度。蓝色越深，完成度越高。");
    for (int level = 0; level < 5; ++level) {
        const int start = level * 20;
        const string label = level == 4
            ? "80%–100%"
            : to_string(start) + "%–" + to_string(start + 19) + "%";
        content->append(*legend_row(
            "graph-completion-swatch-" + to_string(level), label));
    }

    frame->set_child(*content);
    return frame;
}

} // namespace

Gtk::Widget* make_knowledge_graph_view(
    const KnowledgeGraph& graph,
    function<void(const string& chapter_name)> on_open) {
    auto* body = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::HORIZONTAL, 36);
    body->add_css_class("knowledge-graph-view");
    body->set_hexpand(true);
    body->set_halign(Gtk::Align::FILL);
    body->set_valign(Gtk::Align::START);

    auto* graph_column = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, 10);
    graph_column->set_hexpand(true);
    auto* hint = Gtk::make_managed<Gtk::Label>(
        "自上而下按前置依赖分层；章节节点同时显示重要度、掌握程度和完成程度。");
    hint->set_halign(Gtk::Align::START);
    hint->add_css_class("dim-label");
    hint->add_css_class("knowledge-graph-hint");
    graph_column->append(*hint);

    if (graph.empty()) {
        auto* empty = Gtk::make_managed<Gtk::Label>("本分类暂无知识图谱数据。");
        empty->add_css_class("dim-label");
        graph_column->append(*empty);
    } else {
        graph_column->append(*make_canvas(graph, on_open));
    }

    body->append(*graph_column);
    body->append(*make_legend());
    return body;
}
