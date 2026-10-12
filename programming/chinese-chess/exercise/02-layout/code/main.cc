#include "wood.hh"

#include <gtkmm.h>

namespace {

const char* k_css =
    "window { background: #f4ecdf; }"
    "headerbar { background: #7a2e2e; color: white; }"
    "headerbar label { color: white; font-weight: 700; }"
    ".side { background: #fbf6ee; }"
    ".player { font-size: 18px; font-weight: 700; }";

// 代码版：同一套布局，盒子和按钮在这里装。不读 window.blp。
// 棋盘仍是 Wood。按钮只占位置，不接 signal_clicked。
class ChessWindow : public Gtk::ApplicationWindow {
public:
    ChessWindow() {
        set_title("中国象棋");
        set_default_size(1100, 760);

        auto css = Gtk::CssProvider::create();
        css->load_from_string(k_css);
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        auto header = Gtk::make_managed<Gtk::HeaderBar>();
        auto title = Gtk::make_managed<Gtk::Label>("中国象棋");
        header->set_title_widget(*title);
        header->set_show_title_buttons(true);
        set_titlebar(*header);

        auto root = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL);
        auto body = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 12);
        body->set_margin(12);

        auto side = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 8);
        side->add_css_class("side");
        side->set_margin(12);
        side->set_size_request(260, -1);

        auto black = Gtk::make_managed<Gtk::Label>("黑方");
        black->add_css_class("player");
        black->set_halign(Gtk::Align::START);
        auto red = Gtk::make_managed<Gtk::Label>("红方");
        red->add_css_class("player");
        red->set_halign(Gtk::Align::START);
        auto moves = Gtk::make_managed<Gtk::Label>("棋谱出现在这里");
        moves->set_vexpand(true);
        moves->set_valign(Gtk::Align::START);
        auto buttons = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 8);
        auto again = Gtk::make_managed<Gtk::Button>("新局");
        auto undo = Gtk::make_managed<Gtk::Button>("悔棋");
        again->set_sensitive(false);
        undo->set_sensitive(false);
        buttons->append(*again);
        buttons->append(*undo);
        side->append(*black);
        side->append(*moves);
        side->append(*red);
        side->append(*buttons);

        body->append(*Gtk::make_managed<Wood>());
        body->append(*side);

        auto status = Gtk::make_managed<Gtk::Label>("布局先占住位置，按钮先不做事。");
        status->set_margin(8);
        status->set_halign(Gtk::Align::START);
        root->append(*body);
        root->append(*status);
        set_child(*root);
    }
};

}  // namespace

int main(int argc, char* argv[]) {
    auto app = Gtk::Application::create("cn.athena.chinese_chess.ch02",
                                        Gio::Application::Flags::NON_UNIQUE);
    return app->make_window_and_run<ChessWindow>(argc, argv);
}
