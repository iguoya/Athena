#pragma once

#include <gtkmm.h>

#include <string>
#include <vector>

using namespace std;

struct MarkdownHeading {
    string title;
    unsigned level = 1;
    int text_offset = 0;
};

// 将 Markdown 渲染到原生 Gtk::TextView，并返回可用于目录导航的标题位置。
vector<MarkdownHeading> render_markdown(
    Gtk::TextView& text_view,
    const string& markdown);
