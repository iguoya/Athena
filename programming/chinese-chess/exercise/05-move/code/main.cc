#include "session.hh"

#include <gtkmm.h>

namespace {

const char* k_css =
    "window { background: #f4ecdf; }"
    "headerbar { background: #7a2e2e; color: white; }"
    "headerbar label { color: white; font-weight: 700; }"
    ".side { background: #fbf6ee; }"
    ".player { font-size: 18px; font-weight: 700; }"
    "textview { font-size: 16px; }"
    "button.play { background: #7a2e2e; color: white; }";

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

        black_.add_css_class("player");
        black_.set_halign(Gtk::Align::START);
        red_.add_css_class("player");
        red_.set_halign(Gtk::Align::START);
        moves_.set_editable(false);
        moves_.set_cursor_visible(false);
        moves_.set_wrap_mode(Gtk::WrapMode::WORD_CHAR);
        moves_.set_vexpand(true);
        auto scroll = Gtk::make_managed<Gtk::ScrolledWindow>();
        scroll->set_policy(Gtk::PolicyType::NEVER, Gtk::PolicyType::AUTOMATIC);
        scroll->set_vexpand(true);
        scroll->set_child(moves_);

        auto buttons = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 8);
        new_game_.set_label("新局");
        undo_.set_label("悔棋");
        new_game_.add_css_class("play");
        buttons->append(new_game_);
        buttons->append(undo_);

        side->append(black_);
        side->append(*scroll);
        side->append(red_);
        side->append(*buttons);

        body->append(session_.board());
        body->append(*side);
        status_.set_margin(8);
        status_.set_halign(Gtk::Align::START);
        root->append(*body);
        root->append(status_);
        set_child(*root);

        // 控件是上面用代码装的。bind 的参数和界面文件版同一套，规则不用写第二份。
        session_.bind(status_, black_, red_, moves_, new_game_, undo_);
    }

private:
    Session session_;
    Gtk::Label status_;
    Gtk::Label black_;
    Gtk::Label red_;
    Gtk::TextView moves_;
    Gtk::Button new_game_;
    Gtk::Button undo_;
};

}  // namespace

int main(int argc, char* argv[]) {
    auto app = Gtk::Application::create("cn.athena.chinese_chess.ch05",
                                        Gio::Application::Flags::NON_UNIQUE);
    return app->make_window_and_run<ChessWindow>(argc, argv);
}
