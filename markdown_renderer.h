#pragma once

#include <gtkmm.h>

#include <string>
#include <vector>

using namespace std;

struct MarkdownHeading {
    string title;
    string anchor;
    unsigned level = 1;
    int text_offset = 0;
};

// 将 Markdown 渲染到原生 Gtk::TextView，并返回可用于目录导航的标题位置。
vector<MarkdownHeading> render_markdown(
    Gtk::TextView& text_view,
    const string& markdown);

// 将 Markdown 转换成供平台 WebView 使用的完整 HTML 文档。
// 标题会获得与 MarkdownHeading::anchor 一致的稳定页内锚点。
string render_markdown_html(
    const string& markdown,
    const string& stylesheet,
    const vector<MarkdownHeading>& headings);
