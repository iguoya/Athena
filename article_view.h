#pragma once

#include <gtkmm.h>

#include <functional>
#include <memory>
#include <string>

using namespace std;

namespace athena {

// 文章阅读控件的跨平台边界。Markdown 到 HTML 的转换属于共享层，
// 具体平台只负责把同一份 HTML 显示出来。
class ArticleView {
public:
    virtual ~ArticleView() = default;

    virtual void load_html(const string& html, const string& base_path) = 0;
    virtual void scroll_to_anchor(const string& anchor) = 0;
};

// 当前在 macOS 上返回 WKWebView 后端；没有可用原生后端时返回空指针，
// 调用方继续使用 Blueprint 中的 GtkTextView 降级阅读器。
unique_ptr<ArticleView> create_platform_article_view(
    Gtk::DrawingArea& host,
    Gtk::Window& window,
    function<void()> on_unavailable);

} // namespace athena
