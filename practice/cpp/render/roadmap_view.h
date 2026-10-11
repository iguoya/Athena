#pragma once

#include "registry/chapter_catalog.h"

#include <gtkmm.h>

#include <functional>
#include <map>
#include <string>
#include <utility>
#include <vector>

using namespace std;

// 知识点路线图：节点是本章的知识点，箭头是 requires 先修关系，配色与标注
// 取自难度和掌握目标，底部细条是当前熟练度——全部来自 ChapterCatalog 与
// 学习库，手抄任何一项都会和 athena.json 漂移（ADR 0033、0036）。
//
// 同一个组件可以编码不同维度：color_by 决定配色表达难度还是掌握目标。
// 一个通道只承载一个维度（AGENTS.md），但**哪个维度上色由这张图要回答什么
// 问题决定**——导览图问"哪个重哪个难"就让配色表达难度，大纲里服务于掌握
// 目标分档的那张就让配色表达掌握目标。不要反过来先定一条"配色只能表示 X"
// 的规矩再去套。
//
// 不引图表库，理由同 render/chart_view：数据规模很小、图形种类单一。
class RoadmapView final {
public:
    enum class ColorBy { MasteryGoal, Difficulty };

    struct Options {
        ColorBy color_by = ColorBy::MasteryGoal;
        // 在节点第二行写掌握目标。配色已经表达掌握目标时就不必再写一遍。
        bool show_goal_text = false;
        // 底部细条显示当前熟练度；没有记录时留空槽，一眼看出哪几节没开始。
        bool show_progress = true;
    };

    // on_open 收到被点击知识点的稳定 name（subchapter.name），可以为空。
    RoadmapView(
        const ChapterMeta& chapter,
        Options options,
        function<void(const string& subchapter_name)> on_open);

    Gtk::Widget& widget() const;

    // 熟练度变化后调用，重算并重绘。
    void set_mastery(const map<string, int>& mastery_by_id);

private:
    struct Node {
        string name;
        string title;
        MasteryGoal goal = MasteryGoal::Unrated;
        int difficulty = 0;  // 1-5，0 表示尚未评定
        int mastery = 0;     // 0-5
        double x = 0.0;
        double y = 0.0;
        double width = 0.0;
        double height = 0.0;
    };

    void draw(const Cairo::RefPtr<Cairo::Context>& cr, int width, int height);
    void on_pressed(double x, double y);

    const ChapterMeta& m_chapter;
    Options m_options;
    function<void(const string&)> m_on_open;
    Gtk::DrawingArea* m_area = nullptr;
    vector<Node> m_nodes;
    // 先修边，存的是 m_nodes 的下标：first 是先修，second 依赖它。
    vector<pair<size_t, size_t>> m_edges;
};
