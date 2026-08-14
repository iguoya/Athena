#include "article_view.h"

unique_ptr<ArticleView> create_platform_article_view(
    Gtk::DrawingArea&,
    Gtk::Window&) {
    return {};
}
