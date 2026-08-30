#include "chapter_index_page.h"

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
    auto* card = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 14);
    card->add_css_class("roadmap-card");

    auto* heading = Gtk::make_managed<Gtk::Label>("学习路线");
    heading->add_css_class("title-4");
    heading->set_halign(Gtk::Align::START);
    card->append(*heading);

    auto* row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 12);
    row->set_homogeneous(true);
    for (const auto& stage : stages) {
        auto* cell = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 6);
        cell->add_css_class("roadmap-stage");
        cell->set_hexpand(true);

        auto* icon = make_icon_image(stage.icon, 32);
        if (!stage.accent.empty()) {
            icon->add_css_class(stage.accent);
        }
        cell->append(*icon);

        auto* title = Gtk::make_managed<Gtk::Label>(stage.title);
        title->add_css_class("heading");
        title->set_halign(Gtk::Align::START);
        cell->append(*title);

        auto* summary = Gtk::make_managed<Gtk::Label>(stage.summary);
        summary->add_css_class("caption");
        summary->add_css_class("dim-label");
        summary->set_wrap(true);
        summary->set_xalign(0.0F);
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
    column->set_halign(Gtk::Align::CENTER);
    column->set_valign(Gtk::Align::START);

    if (!spec.roadmap.empty()) {
        column->append(*make_roadmap(spec.roadmap));
    }

    auto* heading = Gtk::make_managed<Gtk::Label>(spec.category_title + " · 章节");
    heading->add_css_class("title-2");
    heading->set_halign(Gtk::Align::START);
    column->append(*heading);

    auto* chapter_grid = make_grid();
    for (const auto& entry : spec.chapters) {
        chapter_grid->append(*make_tile(entry, spec.on_open));
    }
    column->append(*chapter_grid);

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
