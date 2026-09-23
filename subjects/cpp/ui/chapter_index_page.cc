#include "chapter_index_page.h"

#include "render/knowledge_graph_view.h"
#include "ui/progress_overview.h"
#include "ui/icon_utils.h"

using namespace std;

namespace {

Gtk::Button* make_tile(
    const ChapterIndexEntry& entry,
    const function<void(const string&)>& on_open) {
    auto* tile = Gtk::make_managed<Gtk::Button>();
    tile->add_css_class("home-tile");
    tile->set_tooltip_text(entry.description);

    auto* box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 10);
    box->set_halign(Gtk::Align::CENTER);
    box->set_valign(Gtk::Align::CENTER);
    box->append(*make_icon_image(entry.icon, 36));

    auto* title = Gtk::make_managed<Gtk::Label>(entry.title);
    title->add_css_class("home-tile-title");
    box->append(*title);

    auto* description = Gtk::make_managed<Gtk::Label>(entry.description);
    description->add_css_class("home-tile-desc");
    description->set_wrap(true);
    description->set_justify(Gtk::Justification::CENTER);
    description->set_max_width_chars(28);
    box->append(*description);

    tile->set_child(*box);
    tile->signal_clicked().connect(
        [on_open, key = entry.key]() { on_open(key); });
    return tile;
}

Gtk::Widget* make_roadmap(const vector<ChapterIndexStage>& stages) {
    auto* card = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 18);
    card->add_css_class("roadmap-card");
    // 之前欢迎页的路线预览占整页宽（width-request 1244），换到索引页后
    // 索引页外层是居中列，不给宽度就会被章节网格挤窄、五格显得局促。
    // 这里显式给一个宽敞的下限，跟旧版观感一致。
    card->set_size_request(1120, -1);

    auto* heading = Gtk::make_managed<Gtk::Label>("学习路线预览");
    heading->add_css_class("title-3");
    heading->set_halign(Gtk::Align::CENTER);
    card->append(*heading);

    auto* row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 16);
    row->set_homogeneous(true);
    for (const auto& stage : stages) {
        auto* cell = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 10);
        cell->add_css_class("roadmap-stage");
        cell->set_hexpand(true);

        auto* icon = make_icon_image(stage.icon, 40);
        icon->set_halign(Gtk::Align::CENTER);
        if (!stage.accent.empty()) {
            icon->add_css_class(stage.accent);
        }
        cell->append(*icon);

        auto* title = Gtk::make_managed<Gtk::Label>(stage.title);
        title->add_css_class("heading");
        title->set_halign(Gtk::Align::CENTER);
        cell->append(*title);

        auto* summary = Gtk::make_managed<Gtk::Label>(stage.summary);
        summary->add_css_class("caption");
        summary->add_css_class("dim-label");
        summary->set_wrap(true);
        summary->set_justify(Gtk::Justification::CENTER);
        summary->set_halign(Gtk::Align::CENTER);
        cell->append(*summary);

        row->append(*cell);
    }
    card->append(*row);
    return card;
}

Gtk::FlowBox* make_grid() {
    auto* grid = Gtk::make_managed<Gtk::FlowBox>();
    grid->set_orientation(Gtk::Orientation::HORIZONTAL);
    grid->set_selection_mode(Gtk::SelectionMode::NONE);
    grid->set_homogeneous(true);
    grid->set_min_children_per_line(2);
    grid->set_max_children_per_line(4);
    grid->set_row_spacing(20);
    grid->set_column_spacing(20);
    grid->set_halign(Gtk::Align::CENTER);
    grid->set_valign(Gtk::Align::START);
    return grid;
}

} // namespace

Gtk::Widget* make_chapter_index_page(const ChapterIndexSpec& spec) {
    auto* scroller = Gtk::make_managed<Gtk::ScrolledWindow>();
    scroller->set_policy(Gtk::PolicyType::NEVER, Gtk::PolicyType::AUTOMATIC);
    scroller->set_hexpand(true);
    scroller->set_vexpand(true);

    auto* column = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 20);
    column->add_css_class("chapter-index");
    column->set_hexpand(true);
    column->set_halign(Gtk::Align::FILL);
    column->set_valign(Gtk::Align::START);

    if (!spec.roadmap.empty() && !spec.knowledge_graph) {
        column->append(*make_roadmap(spec.roadmap));
    }

    const string heading_text = spec.knowledge_graph
        ? spec.category_title + " · 学习图谱"
        : spec.category_title + " · 章节";
    auto* heading = Gtk::make_managed<Gtk::Label>(heading_text);
    heading->add_css_class("title-2");
    heading->set_halign(Gtk::Align::START);
    column->append(*heading);

    if (spec.progress && spec.progress->total > 0) {
        column->append(*make_progress_overview(*spec.progress, spec.stats));
    }

    if (spec.knowledge_graph) {
        column->append(*make_knowledge_graph_view(
            *spec.knowledge_graph, spec.on_open_chapter));
    } else {
        auto* chapter_grid = make_grid();
        for (const auto& entry : spec.chapters) {
            chapter_grid->append(*make_tile(entry, spec.on_open));
        }
        column->append(*chapter_grid);
    }

    if (!spec.tools.empty()) {
        auto* tools_heading = Gtk::make_managed<Gtk::Label>("学习工具");
        tools_heading->add_css_class("title-3");
        tools_heading->set_halign(Gtk::Align::START);
        tools_heading->set_margin_top(12);
        column->append(*tools_heading);

        auto* tools_grid = make_grid();
        for (const auto& entry : spec.tools) {
            tools_grid->append(*make_tile(entry, spec.on_open));
        }
        column->append(*tools_grid);
    }

    scroller->set_child(*column);
    return scroller;
}
