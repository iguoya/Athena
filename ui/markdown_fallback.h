#pragma once

#include <gtkmm.h>

#include <string>

using namespace std;

// 没有 WebView 后端时（当前是 Linux——ArticleView 尚未接入 WebKitGTK 6.0，
// 见 docs/ARCHITECTURE.md 路线图第 9 条）的降级视图：用只读纯文本控件把
// Markdown 原文显示出来，顶部一行说明为什么没有正常排版。至少让手册内容
// 和 AI 回答可读，而不是留一片空白。
//
// out_text_view 非空时，写回内部 TextView 指针，便于调用方稍后（例如 AI
// 请求返回后）替换内容。
Gtk::Widget* make_markdown_fallback_view(
    const string& markdown, Gtk::TextView** out_text_view = nullptr);
