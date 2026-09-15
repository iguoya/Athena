#include "render/domain_graph_view.h"

#include "render/chart_scale.h"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <string>
#include <string_view>
#include <vector>

using namespace std;

namespace {

// 与 knowledge_graph_view 相同的两个间距常量：2K 宽度下每层按最大并列数
// 划分等宽轨道，节点在轨道内铺开；高度交给 GTK 按内容自然测量。
//
// 布局结构（外壳 + 图例）本应写在 .blp 里，这里仍是纯代码构建——属于
// AGENTS.md「GTK 与 Blueprint 规则」里记的既有欠账，待和 knowledge_graph_view
// 一起重构成 .blp 模板 + 代码只填充动态的分层容器与 DrawingArea。
// 节点卡片固定宽度：内容较多（标题、多枚徽章、简介、用途、难点、状态），
// 刻意不压缩——图整体变宽就靠外层横向滚动看，不牺牲单卡可读性。
constexpr int kNodeWidth = 360;
constexpr int kColumnGap = 36;
constexpr int kLayerGap = 72;
// 图谱下方的说明区块（提示语、图例、关联说明、理论科目）统一按这个宽度
// 换行，跟两张图的宽度大致对齐，不各自按内容撑到不同宽度。这是宽度下限：
// 两张图比它宽时，区块跟着整页宽度一起铺开（见 make_domain_graph_view）。
constexpr int kBlockWidth = 2200;

// 每条边在图上画一个编号小圆，下方「箭头说明」按同一编号批量解释关联原因。
// strong=false 的边是"历史 / 概念来路"，画成虚线、编号圆用灰色。
void draw_edge(
    const Cairo::RefPtr<Cairo::Context>& cr,
    const graphene_rect_t& from,
    const graphene_rect_t& to,
    int number,
    bool strong) {
    const double x0 = from.origin.x + from.size.width / 2.0;
    const double y0 = from.origin.y + from.size.height;
    const double x1 = to.origin.x + to.size.width / 2.0;
    const double y1 = to.origin.y;
    const double midy = (y0 + y1) / 2.0;

    // 连线画得淡、细，退成背景——它会从卡片下方穿过（卡片不透明会盖住
    // 中间段），只在层与层的间隙里露出来，不喧宾夺主。
    const ChartColor line = chart_color(strong ? 0xbcc4ce : 0xd6dbe1);
    cr->set_source_rgb(line.r, line.g, line.b);
    cr->set_line_width(strong ? 1.6 : 1.4);
    if (!strong) {
        cr->set_dash(vector<double>{5.0, 4.0}, 0.0);
    }
    cr->move_to(x0, y0);
    cr->curve_to(x0, midy, x1, midy, x1, y1 - 7);
    cr->stroke();
    cr->unset_dash();

    cr->move_to(x1, y1);
    cr->line_to(x1 - 5.0, y1 - 8);
    cr->line_to(x1 + 5.0, y1 - 8);
    cr->close_path();
    cr->fill();

    // 编号圆：放到目标节点正上方的层间隙里——不放连线中点，跨层的中点会
    // 落在中间那层的卡片上。按来向左右错开一点，减少多条边指向同一节点
    // 时的重叠。
    constexpr double r = 13.0;
    const double lean = x0 < x1 - 1.0 ? -(r + 4.0)
                      : x0 > x1 + 1.0 ? (r + 4.0)
                                      : 0.0;
    const double cx = x1 + lean;
    const double cy = y1 - r - 7.0;
    const ChartColor chip = chart_color(strong ? 0x0a58ca : 0x8a94a2);
    cr->set_source_rgb(chip.r, chip.g, chip.b);
    cr->arc(cx, cy, r, 0.0, 2.0 * std::numbers::pi);
    cr->fill();

    const string text = to_string(number);
    cr->set_source_rgb(1.0, 1.0, 1.0);
    cr->select_font_face(
        "Sans", Cairo::ToyFontFace::Slant::NORMAL,
        Cairo::ToyFontFace::Weight::BOLD);
    cr->set_font_size(15.0);
    Cairo::TextExtents extents;
    cr->get_text_extents(text, extents);
    cr->move_to(
        cx - extents.width / 2.0 - extents.x_bearing,
        cy - extents.height / 2.0 - extents.y_bearing);
    cr->show_text(text);
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

Gtk::Label* make_badge(const string& text, const string& css_class) {
    auto* badge = Gtk::make_managed<Gtk::Label>(text);
    badge->add_css_class("graph-metric-badge");
    badge->add_css_class(css_class);
    return badge;
}

struct TagStyle {
    string label;     // 卡片徽章上的短词，控制在 2-3 字，保证一行放得下
    string css_class;
    string full;      // tooltip 里的完整说法
};

TagStyle verify_style(VerifyMode mode) {
    switch (mode) {
        case VerifyMode::Board:
            return {"开发板", "domain-graph-verify-board",
                    "开发板验证：需要单片机 / 开发板 / SBC"};
        case VerifyMode::Bench:
            return {"硬件", "domain-graph-verify-bench",
                    "硬件验证：需要面包板、仪表、EDA、焊接"};
        case VerifyMode::Code:
        default:
            return {"编程", "domain-graph-verify-code",
                    "编程验证：开发机上写代码、运行、看输出"};
    }
}

TagStyle track_style(DomainTrack track) {
    switch (track) {
        case DomainTrack::Engineering:
            return {"结构与工程", "domain-graph-track-engineering", ""};
        case DomainTrack::Systems:
            return {"系统", "domain-graph-track-systems", ""};
        case DomainTrack::Hardware:
            return {"电路与嵌入式", "domain-graph-track-hardware", ""};
        case DomainTrack::AI:
            return {"模型与端侧", "domain-graph-track-ai", ""};
        case DomainTrack::Capstone:
            return {"综合应用", "domain-graph-track-capstone", ""};
        case DomainTrack::Language:
        default:
            return {"编程语言", "domain-graph-track-language", ""};
    }
}

TagStyle priority_style(DomainPriority priority) {
    switch (priority) {
        case DomainPriority::Core:
            return {"核心", "domain-graph-priority-core",
                    "核心主线：多数方向都要，尽量先推进"};
        case DomainPriority::Optional:
            return {"可选", "domain-graph-priority-optional",
                    "可选方向：强方向相关，按需要选"};
        case DomainPriority::Recommended:
        default:
            return {"建议", "domain-graph-priority-recommended",
                    "建议学习：按方向取舍"};
    }
}

Gtk::Label* make_field(const string& prefix, const string& body) {
    auto* label = Gtk::make_managed<Gtk::Label>(prefix + body);
    label->set_halign(Gtk::Align::START);
    label->set_xalign(0.0F);
    label->set_wrap(true);
    label->set_wrap_mode(Pango::WrapMode::WORD_CHAR);
    label->add_css_class("domain-graph-field");
    return label;
}

Gtk::Button* make_node_button(
    const DomainNode& node,
    const function<void(const string&)>& on_open) {
    auto* button = Gtk::make_managed<Gtk::Button>();
    button->set_size_request(kNodeWidth, -1);
    button->set_valign(Gtk::Align::START);
    button->add_css_class("knowledge-graph-node");
    button->add_css_class("domain-graph-node");
    // 左侧色条按领域分组，把同族节点在图上聚成一眼可辨的簇。
    button->add_css_class(track_style(node.track).css_class);

    // 独立应用承载的领域同样可点，只是点击后启动的是另一个程序（ADR 0032）。
    const bool interactive = node.kind == DomainKind::Available
        || node.kind == DomainKind::ExternalApp;
    if (!interactive) {
        button->add_css_class("domain-graph-node-planned");
    }
    if (node.kind == DomainKind::ExternalApp) {
        button->add_css_class("domain-graph-node-app");
    }
    button->set_sensitive(interactive);

    auto* content = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, 10);
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

    // 徽章行：入门起点 + 优先级 + 验证方式。只放短词，保证在固定卡宽内
    // 一行放得下（长的"需要 …"条件另起一行，见下方）。
    auto* tags = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
    tags->set_halign(Gtk::Align::START);
    if (node.entry) {
        tags->append(*make_badge("▶ 入门", "domain-graph-badge-entry"));
    }
    const TagStyle ps = priority_style(node.priority);
    tags->append(*make_badge(ps.label, ps.css_class));
    const TagStyle vs = verify_style(node.verify);
    tags->append(*make_badge(vs.label, vs.css_class));
    content->append(*tags);

    auto* body = Gtk::make_managed<Gtk::Label>(node.content);
    body->set_halign(Gtk::Align::START);
    body->set_xalign(0.0F);
    body->set_wrap(true);
    body->set_wrap_mode(Pango::WrapMode::WORD_CHAR);
    body->add_css_class("knowledge-graph-node-description");
    content->append(*body);

    if (!node.purpose.empty()) {
        content->append(*make_field("用途：", node.purpose));
    }
    if (!node.difficulty.empty()) {
        content->append(*make_field("难点：", node.difficulty));
    }
    if (!node.note.empty()) {
        content->append(*make_field("需要：", node.note));
    }

    // 状态 / 进度。
    if (node.kind == DomainKind::Available) {
        content->append(*make_badge(
            node.total > 0 ? to_string(node.total) + " 个知识点"
                           : string("暂无知识点"),
            "domain-graph-badge-open"));
        auto* completion = Gtk::make_managed<Gtk::ProgressBar>();
        completion->set_fraction(clamp(node.completion, 0.0, 1.0));
        completion->set_show_text(true);
        completion->set_text(
            "完成 " +
            to_string(static_cast<int>(lround(node.completion * 100))) + "%");
        completion->add_css_class("graph-completion");
        completion->add_css_class(
            "graph-completion-" + to_string(completion_level(node.completion)));
        content->append(*completion);
    } else if (node.kind == DomainKind::ExternalApp) {
        auto* row = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 7);
        row->set_halign(Gtk::Align::START);
        row->append(*make_badge("独立应用", "domain-graph-badge-app"));
        content->append(*row);
    } else {
        auto* planned = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 7);
        planned->set_halign(Gtk::Align::START);
        planned->append(*make_badge("规划中", "domain-graph-badge-planned"));
        content->append(*planned);
    }

    button->set_child(*content);

    string tooltip = node.title + "\n" + node.content + "\n用途：" +
        node.purpose;
    if (!node.difficulty.empty()) {
        tooltip += "\n难点：" + node.difficulty;
    }
    if (!node.note.empty()) {
        tooltip += "\n需要：" + node.note;
    }
    tooltip += "\n" + ps.full + "\n" + vs.full;
    if (node.kind == DomainKind::Available) {
        tooltip += "\n已开放 " + to_string(node.total) + " 个知识点，完成 " +
            to_string(static_cast<int>(lround(node.completion * 100))) + "%";
    } else if (node.kind == DomainKind::ExternalApp) {
        tooltip += "\n由独立应用承载，点击启动它自己的窗口";
    } else {
        tooltip += "\n规划中，尚未开放";
    }
    button->set_tooltip_text(tooltip);

    if (interactive) {
        button->signal_clicked().connect(
            [on_open, id = node.id]() { on_open(id); });
    }
    return button;
}

// 单个方向的图：只排 node.side == side 的节点，按各自的 layer/slot 分层，
// 只画两端都在本方向的边（编号沿用 graph.edges 里的全局下标 + 1）。
Gtk::Widget* make_canvas(
    const DomainGraph& graph,
    GraphSide side,
    int layer_count,
    const function<void(const string&)>& on_open) {
    auto* overlay = Gtk::make_managed<Gtk::Overlay>();
    overlay->set_halign(Gtk::Align::START);
    overlay->set_valign(Gtk::Align::START);

    int column_count = 1;
    for (const auto& node : graph.nodes) {
        if (node.side == side) {
            column_count = max(column_count, node.layer_size);
        }
    }
    // 每层等宽的固定总宽——节点不随窗口压缩，窄了就横向滚动。
    const int row_width =
        column_count * kNodeWidth + (column_count - 1) * kColumnGap;

    auto* layers = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, kLayerGap);
    layers->set_halign(Gtk::Align::START);

    vector<Gtk::Button*> node_widgets(graph.nodes.size(), nullptr);
    for (int layer = 0; layer < layer_count; ++layer) {
        auto* row = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, kColumnGap);
        row->set_halign(Gtk::Align::START);
        row->set_size_request(row_width, -1);
        row->add_css_class("domain-graph-layer");
        row->add_css_class(layer % 2 == 0 ? "domain-graph-layer-even"
                                          : "domain-graph-layer-odd");

        vector<int> node_at_column(static_cast<size_t>(column_count), -1);
        for (size_t index = 0; index < graph.nodes.size(); ++index) {
            const auto& node = graph.nodes[index];
            if (node.side != side || node.layer != layer) {
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
                spacer->set_size_request(kNodeWidth, -1);
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
    edges->set_can_target(false);
    edges->set_draw_func(
        [graph, node_widgets, overlay, side](
            const Cairo::RefPtr<Cairo::Context>& cr, int, int) {
            for (size_t i = 0; i < graph.edges.size(); ++i) {
                const auto& edge = graph.edges[i];
                if (graph.nodes[static_cast<size_t>(edge.from)].side != side) {
                    continue;
                }
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
                    draw_edge(cr, from, to, static_cast<int>(i) + 1,
                              edge.strong);
                }
            }
        });
    // 图和下方图例之间留一点空隙。
    layers->set_margin_bottom(12);

    overlay->add_overlay(*edges);

    // 直接返回这个固定尺寸的 overlay：自然宽 = 层宽（约 column_count ×
    // kNodeWidth），自然高 = 各层高度之和，都是确定值。不再自己套横向
    // ScrolledWindow——那一层 + 里面的 Overlay 会让高度传播算不准，
    // 表现为最后一层卡片被下方内容盖住。横向滚动交给首页外层的
    // ScrolledWindow（window.blp 里已放开为 automatic）。
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

// 图例的一组：小标题 + 若干色块行，纵向排一列。
Gtk::Widget* legend_group(
    const string& title,
    const string& note,
    const vector<pair<string, string>>& rows) {
    auto* box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 6);
    box->add_css_class("domain-graph-legend-group");

    auto* heading = Gtk::make_managed<Gtk::Label>(title);
    heading->set_halign(Gtk::Align::START);
    heading->add_css_class("heading");
    box->append(*heading);

    if (!note.empty()) {
        auto* label = Gtk::make_managed<Gtk::Label>(note);
        label->set_halign(Gtk::Align::START);
        label->set_xalign(0.0F);
        label->set_wrap(true);
        label->add_css_class("dim-label");
        label->add_css_class("knowledge-graph-legend-note");
        box->append(*label);
    }
    for (const auto& [css_class, text] : rows) {
        box->append(*legend_row(css_class, text));
    }
    return box;
}

// 全宽图例区：分组横向铺开（FlowBox 自适应换行），不再挤在右侧窄栏。
Gtk::Widget* make_legend() {
    auto* frame = Gtk::make_managed<Gtk::Frame>("图例");
    frame->add_css_class("panel-frame");
    frame->add_css_class("group-frame");
    frame->add_css_class("knowledge-graph-legend");

    auto* flow = Gtk::make_managed<Gtk::FlowBox>();
    flow->set_margin(14);
    flow->set_selection_mode(Gtk::SelectionMode::NONE);
    flow->set_row_spacing(16);
    flow->set_column_spacing(28);
    flow->set_min_children_per_line(1);
    flow->set_max_children_per_line(5);

    flow->append(*legend_group(
        "领域分组（左侧色条）",
        "同色是同一学习方向，在图上聚成一簇：",
        {{"domain-graph-track-swatch-language", "编程语言：C++ / C / Python"},
         {"domain-graph-track-swatch-engineering", "结构与工程：算法、设计模式、工具链"},
         {"domain-graph-track-swatch-systems", "系统：系统编程、并发、网络、操作系统"},
         {"domain-graph-track-swatch-hardware", "电路与嵌入式：电路、单片机、PCB、RTOS"},
         {"domain-graph-track-swatch-ai", "模型与端侧：模型开发、端侧 AI"},
         {"domain-graph-track-swatch-capstone", "综合应用"}}));

    flow->append(*legend_group(
        "优先级（徽章）",
        "分层已是推荐次序，这里区分主次：",
        {{"domain-graph-priority-swatch-core", "核心主线：多数方向都要，先推进"},
         {"domain-graph-priority-swatch-recommended", "建议学习：按方向取舍"},
         {"domain-graph-priority-swatch-optional", "可选方向：强方向相关"}}));

    flow->append(*legend_group(
        "验证方式（徽章）",
        "图谱只收能验证的实践科目：",
        {{"domain-graph-verify-swatch-code", "编程验证：写代码、跑、看输出"},
         {"domain-graph-verify-swatch-board", "开发板验证：单片机 / 开发板 / SBC"},
         {"domain-graph-verify-swatch-bench", "硬件验证：面包板、仪表、EDA、焊接"}}));

    flow->append(*legend_group(
        "领域状态",
        "",
        {{"domain-graph-swatch-open", "已开放：点击进入，进度条为掌握程度"},
         {"domain-graph-swatch-planned", "规划中：方向已定，尚未开放"}}));

    vector<pair<string, string>> completion_rows;
    for (int level = 0; level < 5; ++level) {
        const int start = level * 20;
        completion_rows.push_back(
            {"graph-completion-swatch-" + to_string(level),
             level == 4 ? "80%–100%"
                        : to_string(start) + "%–" + to_string(start + 19) + "%"});
    }
    flow->append(*legend_group(
        "完成程度",
        "按该分类平均熟练度 ÷ 5 计算，蓝色越深越高。",
        completion_rows));

    frame->set_child(*flow);
    return frame;
}

void append_edge_row(
    Gtk::Grid& grid,
    int& row,
    int number,
    const string& pair_text,
    const string& reason_text,
    bool strong) {
    auto* num = Gtk::make_managed<Gtk::Label>(to_string(number));
    num->add_css_class("domain-graph-edge-number");
    if (!strong) {
        num->add_css_class("domain-graph-edge-number-weak");
    }
    num->set_valign(Gtk::Align::START);
    grid.attach(*num, 0, row);

    auto* pair = Gtk::make_managed<Gtk::Label>(pair_text);
    pair->set_halign(Gtk::Align::START);
    pair->set_xalign(0.0F);
    pair->set_wrap(true);
    pair->add_css_class("domain-graph-edge-pair");
    grid.attach(*pair, 1, row);

    auto* reason = Gtk::make_managed<Gtk::Label>(reason_text);
    reason->set_halign(Gtk::Align::START);
    reason->set_xalign(0.0F);
    reason->set_wrap(true);
    reason->set_hexpand(true);
    reason->add_css_class("dim-label");
    grid.attach(*reason, 2, row);
    ++row;
}

// 全宽区块：按图上编号逐条说明关联的历史 / 概念来路和学习必要性。
// 方向内依赖在前，两张图之间的关联在后，编号连续。
Gtk::Widget* make_edge_notes(const DomainGraph& graph) {
    auto* frame = Gtk::make_managed<Gtk::Frame>(
        "关联说明 · 每条箭头的来路与学它的必要性");
    frame->add_css_class("panel-frame");
    frame->add_css_class("group-frame");
    frame->add_css_class("domain-graph-edge-notes");

    auto* box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 10);
    box->set_margin(14);

    auto* legend = Gtk::make_managed<Gtk::Label>(
        "实线 = 前置门槛（离开前者基本学不动后者）；"
        "虚线 = 历史 / 概念上的来路（知道渊源会更透彻，但不是必须先学）。");
    legend->set_halign(Gtk::Align::START);
    legend->set_xalign(0.0F);
    legend->set_wrap(true);
    legend->add_css_class("dim-label");
    box->append(*legend);

    const auto title_of = [&graph](int i) -> const string& {
        return graph.nodes[static_cast<size_t>(i)].title;
    };

    auto* inner_head = Gtk::make_managed<Gtk::Label>("方向内的依赖");
    inner_head->set_halign(Gtk::Align::START);
    inner_head->add_css_class("heading");
    box->append(*inner_head);

    auto* inner_grid = Gtk::make_managed<Gtk::Grid>();
    inner_grid->set_row_spacing(8);
    inner_grid->set_column_spacing(14);
    int inner_row = 0;
    for (size_t i = 0; i < graph.edges.size(); ++i) {
        const auto& e = graph.edges[i];
        append_edge_row(
            *inner_grid, inner_row, static_cast<int>(i) + 1,
            title_of(e.from) + " → " + title_of(e.to), e.reason, e.strong);
    }
    box->append(*inner_grid);

    if (!graph.cross_edges.empty()) {
        auto* cross_head = Gtk::make_managed<Gtk::Label>(
            "两张图之间的关联（跨方向）");
        cross_head->set_halign(Gtk::Align::START);
        cross_head->add_css_class("heading");
        cross_head->set_margin_top(6);
        box->append(*cross_head);

        auto* cross_grid = Gtk::make_managed<Gtk::Grid>();
        cross_grid->set_row_spacing(8);
        cross_grid->set_column_spacing(14);
        int cross_row = 0;
        for (size_t j = 0; j < graph.cross_edges.size(); ++j) {
            const auto& e = graph.cross_edges[j];
            append_edge_row(
                *cross_grid, cross_row,
                static_cast<int>(graph.edges.size() + j) + 1,
                title_of(e.from) + " → " + title_of(e.to), e.reason, e.strong);
        }
        box->append(*cross_grid);
    }

    frame->set_child(*box);
    return frame;
}

// 全宽区块：不建节点的理论科目，内容与作用分开。
Gtk::Widget* make_theory_section(const DomainGraph& graph) {
    auto* frame = Gtk::make_managed<Gtk::Frame>(
        "理论科目 · 不建节点，建议配合教材了解");
    frame->add_css_class("panel-frame");
    frame->add_css_class("group-frame");
    frame->add_css_class("domain-graph-theory");

    auto* flow = Gtk::make_managed<Gtk::FlowBox>();
    flow->set_margin(14);
    flow->set_selection_mode(Gtk::SelectionMode::NONE);
    flow->set_row_spacing(12);
    flow->set_column_spacing(12);
    flow->set_min_children_per_line(1);
    flow->set_max_children_per_line(3);
    flow->set_homogeneous(true);

    for (const auto& topic : graph.theory) {
        auto* card = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::VERTICAL, 6);
        card->add_css_class("domain-graph-theory-card");

        auto* name = Gtk::make_managed<Gtk::Label>(topic.name);
        name->set_halign(Gtk::Align::START);
        name->add_css_class("heading");
        card->append(*name);
        card->append(*make_field("内容：", topic.content));
        card->append(*make_field("作用：", topic.role));

        flow->append(*card);
    }

    frame->set_child(*flow);
    return frame;
}

} // namespace

Gtk::Widget* make_domain_graph_view(
    const DomainGraph& graph,
    function<void(const string& domain_id)> on_open) {
    auto* outer = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::VERTICAL, 24);
    outer->add_css_class("knowledge-graph-view");
    outer->add_css_class("domain-graph-view");
    outer->set_halign(Gtk::Align::START);
    outer->set_valign(Gtk::Align::START);

    auto* hint = Gtk::make_managed<Gtk::Label>(
        "分两张图：计算机（软件 / 系统）方向和电子信息（电路 / 嵌入式）"
        "方向，各自成图，跨方向的关联单独列在下方。纵轴是知识的来路与"
        "依赖，不是难度或强制次序——带 ▶ 的是推荐入门起点，从任意一个"
        "开始都行。左侧色条按领域分组，徽章标优先级和验证方式。已开放的"
        "点开进入，灰色是规划中的方向。图较宽，窄窗口时整页可左右滚动。");
    hint->set_halign(Gtk::Align::START);
    hint->set_xalign(0.0F);
    hint->set_wrap(true);
    hint->set_size_request(kBlockWidth, -1);
    hint->add_css_class("dim-label");
    hint->add_css_class("knowledge-graph-hint");
    outer->append(*hint);

    if (graph.empty()) {
        auto* empty = Gtk::make_managed<Gtk::Label>("暂无学科图谱数据。");
        empty->add_css_class("dim-label");
        outer->append(*empty);
        return outer;
    }

    const auto side_section = [&](const string& title, GraphSide side,
                                  int layer_count) {
        auto* frame = Gtk::make_managed<Gtk::Frame>(title);
        frame->add_css_class("panel-frame");
        frame->add_css_class("group-frame");
        frame->add_css_class("domain-graph-side");
        auto* wrap = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::VERTICAL, 8);
        wrap->set_margin(14);
        wrap->set_halign(Gtk::Align::START);

        auto* canvas = make_canvas(graph, side, layer_count, on_open);
        canvas->set_halign(Gtk::Align::START);
        wrap->append(*canvas);
        frame->set_child(*wrap);
        frame->set_halign(Gtk::Align::START);
        outer->append(*frame);
    };

    side_section("计算机方向 · 软件与系统", GraphSide::Computer,
                 graph.computer_layer_count);
    side_section("电子信息方向 · 电路与嵌入式", GraphSide::Electronics,
                 graph.electronics_layer_count);

    // 说明区块保持 halign 默认的 FILL，铺满整页宽度：换成 START 会让 GTK 按
    // 外层分配到的宽度估算高度、却按收窄后的自身宽度排版，行数变多而高度没
    // 跟着变，换行文字被压掉一截，启动时还会打出 gtk_widget_measure 的尺寸
    // 告警。宽度下限由 kBlockWidth 保证，不需要再靠对齐方式收窄。
    for (Gtk::Widget* block :
         {make_legend(), make_edge_notes(graph), make_theory_section(graph)}) {
        block->set_size_request(kBlockWidth, -1);
        outer->append(*block);
    }
    return outer;
}
