#include "render/knowledge_graph_view.h"

#include "render/chart_scale.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <string_view>

using namespace std;

namespace {

// 节点保留分类索引卡片的信息密度：图标、标题、两行简介和三种学习指标。
// C++ 当前最宽一层只有三个节点，因此无需为了塞进一屏牺牲可读性。
constexpr double kNodeWidth = 244;
constexpr double kNodeHeight = 168;
constexpr double kGapX = 42;
constexpr double kGapY = 54;
constexpr double kMarginX = 32;
constexpr double kMarginY = 30;

struct NodePlacement {
    double x = 0;
    double y = 0;
    const KnowledgeNode* node = nullptr;
};

struct Layout {
    vector<NodePlacement> placements;
    double width = 0;
    double height = 0;
};

Layout compute_layout(const KnowledgeGraph& graph) {
    Layout layout;
    if (graph.empty()) {
        return layout;
    }

    vector<double> layer_width(
        static_cast<size_t>(graph.layer_count), 0.0);
    for (const auto& node : graph.nodes) {
        const double width =
            node.layer_size * kNodeWidth + (node.layer_size - 1) * kGapX;
        layer_width[static_cast<size_t>(node.layer)] = width;
    }
    const double widest =
        *max_element(layer_width.begin(), layer_width.end());

    layout.width = widest + kMarginX * 2;
    layout.height = graph.layer_count * kNodeHeight
        + (graph.layer_count - 1) * kGapY + kMarginY * 2;

    layout.placements.reserve(graph.nodes.size());
    for (const auto& node : graph.nodes) {
        const double this_layer_width =
            layer_width[static_cast<size_t>(node.layer)];
        const double layer_left =
            kMarginX + (widest - this_layer_width) / 2.0;
        layout.placements.push_back({
            .x = layer_left + node.slot * (kNodeWidth + kGapX),
            .y = kMarginY + node.layer * (kNodeHeight + kGapY),
            .node = &node,
        });
    }
    return layout;
}

void draw_edge(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const NodePlacement& from,
    const NodePlacement& to) {
    const double x0 = from.x + kNodeWidth / 2.0;
    const double y0 = from.y + kNodeHeight;
    const double x1 = to.x + kNodeWidth / 2.0;
    const double y1 = to.y;
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
    button->set_size_request(
        static_cast<int>(kNodeWidth), static_cast<int>(kNodeHeight));
    button->add_css_class("knowledge-graph-node");
    button->add_css_class(
        "graph-importance-" + to_string(clamp(node.importance, 0, 5)));

    auto* content = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, 8);
    content->set_margin(12);

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
    title->set_ellipsize(Pango::EllipsizeMode::END);
    title->add_css_class("knowledge-graph-node-title");
    heading->append(*title);
    content->append(*heading);

    auto* description = Gtk::make_managed<Gtk::Label>(node.description);
    description->set_halign(Gtk::Align::START);
    description->set_xalign(0.0F);
    description->set_wrap(true);
    description->set_wrap_mode(Pango::WrapMode::WORD_CHAR);
    description->set_ellipsize(Pango::EllipsizeMode::END);
    description->set_lines(2);
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
    const Layout layout = compute_layout(graph);
    auto* overlay = Gtk::make_managed<Gtk::Overlay>();
    overlay->set_size_request(
        static_cast<int>(ceil(layout.width)),
        static_cast<int>(ceil(layout.height)));

    auto* edges = Gtk::make_managed<Gtk::DrawingArea>();
    edges->set_content_width(static_cast<int>(ceil(layout.width)));
    edges->set_content_height(static_cast<int>(ceil(layout.height)));
    edges->set_draw_func(
        [graph](const Cairo::RefPtr<Cairo::Context>& cr, int, int) {
            const Layout current = compute_layout(graph);
            for (const auto& edge : graph.edges) {
                draw_edge(
                    cr,
                    current.placements[static_cast<size_t>(edge.from)],
                    current.placements[static_cast<size_t>(edge.to)]);
            }
        });
    overlay->set_child(*edges);

    auto* nodes = Gtk::make_managed<Gtk::Fixed>();
    nodes->set_size_request(
        static_cast<int>(ceil(layout.width)),
        static_cast<int>(ceil(layout.height)));
    for (const auto& placement : layout.placements) {
        nodes->put(
            *make_node_button(*placement.node, on_open),
            placement.x,
            placement.y);
    }
    overlay->add_overlay(*nodes);
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
    frame->set_size_request(286, -1);
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
        Gtk::Orientation::HORIZONTAL, 22);
    body->add_css_class("knowledge-graph-view");
    body->set_halign(Gtk::Align::CENTER);
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
