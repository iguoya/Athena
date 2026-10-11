#pragma once

#include "content/lesson_doc.h"

#include <gtkmm.h>

#include <functional>
#include <string>
#include <vector>

using namespace std;

// 把课文数据渲染成 GTK 控件树（ADR 0055）。
//
// 内容由数据决定，形态由 lesson_blocks.blp 的模板决定，这里只负责按块类型
// 分派并递归处理嵌套。**它不该知道任何一章的具体内容**——一旦出现「如果是
// 某某章就怎样」的分支，说明该加的是块类型，不是分支。
class LessonRenderer final {
public:
    // figure 块按 id 取控件。自绘图仍然是各写各的 Cairo / Snapshot（ADR 0038），
    // 数据只决定它出现在哪一节。返回 nullptr 表示这个 id 没有注册。
    using FigureFactory = function<Gtk::Widget*(const string& id)>;

    explicit LessonRenderer(FigureFactory figures = {});

    // 渲染一个知识点的全部块到 host。
    void render(Gtk::Box& host, const LessonDoc& doc) const;

private:
    void render_blocks(Gtk::Box& host, const vector<LessonBlock>& blocks) const;
    void render_block(Gtk::Box& host, const LessonBlock& block) const;

    FigureFactory m_figures;
};
