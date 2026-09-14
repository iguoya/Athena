#include "progress_overview.h"

#include "render/chart_view.h"

#include <map>

Gtk::Widget* make_progress_overview(const CategoryProgress& progress) {
    auto page = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 16);
    page->set_hexpand(true);
    page->add_css_class("progress-overview");

    // 环形图和统计卡片并排：它们讲的是同一件事（整体进度的两种读法），
    // 分两行反而要来回看。
    auto summary_row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 24);
    page->append(*summary_row);

    auto tiles_row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 16);
    tiles_row->set_homogeneous(true);
    tiles_row->set_hexpand(true);
    tiles_row->set_valign(Gtk::Align::CENTER);

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
    // 第四张卡原来是「平均熟练度 0.6 / 5」：一个被大量未开始知识点拉低的
    // 平均值，既说不清学得怎么样，也指不出下一步。换成还没碰过的数量，
    // 和前三张一起正好是「总数 + 三种状态」。
    add_tile(
        to_string(progress.not_started), "未涉及（0 星）", "stat-tile-average");

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
    summary_row->append(*donut_frame);
    summary_row->append(*tiles_row);

    // 逐个知识点的掌握程度，单开一行占满宽度。原来这里是按星级分档的
    // 直方图，只说得出"有几个在 3 星"，说不出是哪几个——看完并不知道
    // 下一步该补哪里。横轴换成知识点本身，落后的是谁一眼可见。
    //
    // 只收有熟练度记录或所在章节已经开始学的知识点：把 63 个还没动过的
    // 规划中知识点也画上，整张图会被空柱淹没。
    vector<MasteryPoint> points;
    for (const auto& chapter_stat : progress.chapters) {
        if (chapter_stat.mastery_sum <= 0) {
            continue;
        }
        for (const auto& [title, mastery] : chapter_stat.subchapter_mastery) {
            points.push_back(MasteryPoint{
                .chapter_title = chapter_stat.chapter_title,
                .title = title,
                .mastery = mastery,
            });
        }
    }
    if (!points.empty()) {
        auto points_frame = Gtk::make_managed<Gtk::Frame>();
        points_frame->add_css_class("panel-frame");
        points_frame->set_label("各知识点掌握程度");
        points_frame->set_hexpand(true);
        auto points_box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL);
        points_box->set_margin_top(12);
        points_box->set_margin_bottom(12);
        points_box->set_margin_start(12);
        points_box->set_margin_end(12);
        points_box->append(*make_mastery_by_point_chart(points));

        // 序号对照表：图上只有 ①②③，名字放在这里。按章节分行，章节名用
        // 该章在图上的配色，两处编号与颜色必须一致，图例才有意义。
        map<string, size_t> color_index;
        for (const auto& point : points) {
            color_index.emplace(point.chapter_title, color_index.size());
        }
        string current_chapter;
        string line;
        size_t chapter_slot = 0;
        const auto flush_line = [&] {
            if (line.empty()) {
                return;
            }
            auto legend = Gtk::make_managed<Gtk::Label>();
            legend->set_markup(
                "<span foreground='" + chapter_palette_hex(chapter_slot)
                + "' weight='bold'>" + current_chapter + "</span>　" + line);
            legend->set_halign(Gtk::Align::START);
            legend->set_wrap(true);
            legend->set_xalign(0.0);
            legend->add_css_class("chart-legend-line");
            points_box->append(*legend);
            line.clear();
        };
        for (size_t index = 0; index < points.size(); ++index) {
            const auto& point = points[index];
            if (point.chapter_title != current_chapter) {
                flush_line();
                current_chapter = point.chapter_title;
                chapter_slot = color_index.at(current_chapter);
            }
            if (!line.empty()) {
                line += "　";
            }
            line += circled_index(index + 1) + " " + point.title;
        }
        flush_line();

        points_frame->set_child(*points_box);
        page->append(*points_frame);
    }

    // 章节与知识点的逐条进度不在这里重复：它们已经画在学习图谱的章节
    // 卡片上（逐个知识点 + 掌握程度 + 考核成绩）。同一件事只留一个入口。
    return page;
}
