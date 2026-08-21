#include "progress_page.h"

#include "render/chart_view.h"

#include <iomanip>
#include <sstream>

Gtk::Widget* make_progress_page(
    const string& category_title,
    const CategoryProgress& progress) {
    auto scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    scrolled->set_hexpand(true);
    scrolled->set_vexpand(true);
    scrolled->add_css_class("progress-page");

    auto page = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 24);
    page->set_margin_top(28);
    page->set_margin_bottom(28);
    page->set_margin_start(32);
    page->set_margin_end(32);
    scrolled->set_child(*page);

    auto title = Gtk::make_managed<Gtk::Label>("学习进度 · " + category_title);
    title->add_css_class("title-2");
    title->set_halign(Gtk::Align::START);
    page->append(*title);

    auto tiles_row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 16);
    tiles_row->set_homogeneous(true);
    page->append(*tiles_row);

    const auto add_tile =
        [tiles_row](const string& value, const string& label, const string& css_class) {
            auto tile = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 2);
            tile->add_css_class("stat-tile");
            tile->add_css_class(css_class);
            auto value_label = Gtk::make_managed<Gtk::Label>(value);
            value_label->add_css_class("stat-tile-value");
            value_label->set_halign(Gtk::Align::START);
            auto text_label = Gtk::make_managed<Gtk::Label>(label);
            text_label->add_css_class("stat-tile-label");
            text_label->set_halign(Gtk::Align::START);
            tile->append(*value_label);
            tile->append(*text_label);
            tiles_row->append(*tile);
        };

    add_tile(to_string(progress.total), "知识点总数", "stat-tile-total");
    add_tile(to_string(progress.mastered), "已掌握（5 星）", "stat-tile-mastered");
    add_tile(
        to_string(progress.in_progress),
        "学习中（1–4 星）",
        "stat-tile-in-progress");
    ostringstream average_text;
    average_text << fixed << setprecision(1) << progress.average_mastery();
    add_tile(average_text.str() + " / 5", "平均熟练度", "stat-tile-average");

    auto charts_row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 24);
    page->append(*charts_row);

    auto donut_frame = Gtk::make_managed<Gtk::Frame>();
    donut_frame->add_css_class("panel-frame");
    donut_frame->set_label("整体完成度");
    auto donut_box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 10);
    donut_box->set_margin_top(12);
    donut_box->set_margin_bottom(12);
    donut_box->set_margin_start(12);
    donut_box->set_margin_end(12);
    donut_box->set_halign(Gtk::Align::CENTER);
    donut_box->append(*make_mastery_donut_chart(
        progress.mastered, progress.in_progress, progress.not_started));
    donut_box->append(*make_mastery_legend());
    donut_frame->set_child(*donut_box);
    charts_row->append(*donut_frame);

    auto histogram_frame = Gtk::make_managed<Gtk::Frame>();
    histogram_frame->add_css_class("panel-frame");
    histogram_frame->set_label("熟练度分布");
    histogram_frame->set_hexpand(true);
    auto histogram_box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL);
    histogram_box->set_margin_top(12);
    histogram_box->set_margin_bottom(12);
    histogram_box->set_margin_start(12);
    histogram_box->set_margin_end(12);
    histogram_box->append(
        *make_mastery_histogram_chart(progress.mastery_histogram()));
    histogram_frame->set_child(*histogram_box);
    charts_row->append(*histogram_frame);

    for (const auto& chapter_stat : progress.chapters) {
        auto expander = Gtk::make_managed<Gtk::Expander>();
        expander->add_css_class("progress-chapter-row");

        auto header = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 10);
        auto chapter_title = Gtk::make_managed<Gtk::Label>(chapter_stat.chapter_title);
        chapter_title->add_css_class("progress-chapter-title");
        header->append(*chapter_title);

        auto chapter_bar = Gtk::make_managed<Gtk::LevelBar>();
        chapter_bar->set_min_value(0);
        chapter_bar->set_max_value(1.0);
        chapter_bar->set_value(chapter_stat.completion_ratio());
        chapter_bar->set_hexpand(true);
        chapter_bar->set_valign(Gtk::Align::CENTER);
        header->append(*chapter_bar);

        auto chapter_count = Gtk::make_managed<Gtk::Label>(
            to_string(chapter_stat.mastered) + "/" + to_string(chapter_stat.total));
        chapter_count->add_css_class("progress-chapter-count");
        header->append(*chapter_count);
        expander->set_label_widget(*header);

        auto subchapter_list = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 2);
        for (const auto& [sub_title, mastery] : chapter_stat.subchapter_mastery) {
            auto sub_row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 8);
            sub_row->add_css_class("progress-subchapter-row");
            auto sub_label = Gtk::make_managed<Gtk::Label>(sub_title);
            sub_label->set_hexpand(true);
            sub_label->set_halign(Gtk::Align::START);
            sub_row->append(*sub_label);
            sub_row->append(*make_mastery_stars(mastery));
            subchapter_list->append(*sub_row);
        }
        expander->set_child(*subchapter_list);
        page->append(*expander);
    }

    return scrolled;
}
