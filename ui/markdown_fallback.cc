#include "markdown_fallback.h"

using namespace std;

Gtk::Widget* make_markdown_fallback_view(
    const string& markdown, Gtk::TextView** out_text_view) {
    auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 8);
    box->set_hexpand(true);
    box->set_vexpand(true);
    box->set_margin_top(12);
    box->set_margin_bottom(12);
    box->set_margin_start(12);
    box->set_margin_end(12);

    auto notice = Gtk::make_managed<Gtk::Label>(
        "当前平台没有可用的文章渲染后端，以下按 Markdown 原文显示。");
    notice->add_css_class("dim-label");
    notice->set_halign(Gtk::Align::START);
    notice->set_wrap(true);
    box->append(*notice);

    auto scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    scrolled->set_hexpand(true);
    scrolled->set_vexpand(true);
    auto text_view = Gtk::make_managed<Gtk::TextView>();
    text_view->set_editable(false);
    text_view->set_cursor_visible(false);
    text_view->set_monospace(true);
    text_view->set_wrap_mode(Gtk::WrapMode::WORD_CHAR);
    text_view->add_css_class("code-view");
    text_view->get_buffer()->set_text(markdown);
    scrolled->set_child(*text_view);
    box->append(*scrolled);

    if (out_text_view) {
        *out_text_view = text_view;
    }
    return box;
}
