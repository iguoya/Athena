#pragma once

#include <string>
#include <vector>

using namespace std;

struct MarkdownHeading {
    string title;
    string anchor;
    unsigned level = 1;
};

// 提取文章目录所需的标题；正文只通过 WebView 显示。
vector<MarkdownHeading> parse_markdown_headings(const string& markdown);

// 将 Markdown、文章目录和阅读工具栏组合成完整 HTML 文档。
string render_markdown_html(
    const string& markdown,
    const string& stylesheet,
    const vector<MarkdownHeading>& headings);
