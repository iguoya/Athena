#pragma once

#include <gtkmm.h>

#include <memory>
#include <string>

using namespace std;

// 文章阅读控件的跨平台边界。Markdown 到 HTML 的转换属于共享层，
// 具体平台只负责把同一份 HTML 显示出来。
class ArticleView {
public:
    virtual ~ArticleView() = default;

    virtual void load_html(const string& html, const string& base_path) = 0;
};

// 当前在 macOS 上返回 WKWebView 后端；其他平台可在此接口下增加实现。
unique_ptr<ArticleView> create_platform_article_view(
    Gtk::DrawingArea& host,
    Gtk::Window& window);
