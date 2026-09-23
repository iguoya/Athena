#pragma once

#include <gtkmm.h>

#include <string>

using namespace std;

// 课文里 figure 块的 id → 控件（ADR 0055）。
//
// 图仍然是各写各的 Cairo 自绘（ADR 0038），数据只决定它出现在哪一节。
// 这张表是两者之间唯一的接缝：课文写 {"type":"figure","id":"xxx"}，
// 这里把 xxx 映射到一个画好的 DrawingArea。
//
// 认不出的 id 返回 nullptr，渲染器会跳过图只留图注——课文与绘制函数分属
// 数据和代码，允许一方先落地。
Gtk::Widget* make_lesson_figure(const string& id);
