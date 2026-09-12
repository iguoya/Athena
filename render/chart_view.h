#pragma once

#include "registry/progress_stats.h"

#include <gtkmm.h>

using namespace std;

// 学习进度页的 Cairo 手绘图表。
//
// 这一层依赖 GTK/Cairo，不进 athena-core；纯计算（刻度、配色）在
// render/chart_scale.h，聚合口径在 registry/progress_stats.h，那两部分
// 可以脱离 GTK 单独测试。
//
// 不引入图表库：数据规模很小（几十个知识点、十几个章节、一个 0-5 的标量），
// 需要的图表种类有限，Cairo 直接画比接一套 JS 图表栈划算，也不用为此让
// 统计页不依赖 WebView。

// 环形图：已掌握/学习中/未开始三段占比，中心显示已掌握百分比。
Gtk::DrawingArea* make_mastery_donut_chart(
    int mastered,
    int in_progress,
    int not_started);

// 环形图的图例：三个色块对应已掌握/学习中/未开始。
Gtk::Box* make_mastery_legend();

// 熟练度分布直方图：横轴是 0-5 星，纵轴是该星级的知识点数量。
Gtk::DrawingArea* make_mastery_histogram_chart(
    const array<int, kMasteryLevels>& histogram);

// 逐个知识点的掌握程度：横轴一个知识点一根柱，纵轴是 0-5 星。
//
// 它替代按星级分档的直方图：那张图只说得出"有几个在 3 星"，说不出是哪几个，
// 学习者看完并不知道下一步该补哪里。这张图一眼看到具体是哪个知识点落后。
//
// 只画有教学内容的章节——规划中的章节全是 0 星，画出来是一片空柱。
struct MasteryPoint {
    string chapter_title;
    string title;
    int mastery = 0;  // 0-5
};
Gtk::DrawingArea* make_mastery_by_point_chart(const vector<MasteryPoint>& points);

// 只读的五星展示（实心/空心），用于逐章节列表里的单个知识点。
Gtk::Box* make_mastery_stars(int mastery);
