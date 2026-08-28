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
    // 跳到页面内某个标题锚点（如 "athena-heading-3"）；文档还没加载完成
    // 时应记住这个请求，等加载完成后再执行，不丢失。
    virtual void scroll_to_anchor(const string& anchor) = 0;
};

// macOS 使用系统 WKWebView，Ubuntu 使用 WebKitGTK 6.0；其他平台可在此
// 接口下增加实现。
unique_ptr<ArticleView> create_platform_article_view(
    Gtk::DrawingArea& host,
    Gtk::Window& window);
