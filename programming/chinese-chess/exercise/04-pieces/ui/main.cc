#include "board_view.hh"

#include <gtkmm.h>

#include <stdexcept>
#include <string>

namespace {

// 和上一章一样取出窗口。BoardView 里已经按开局摆好子，这里不接点击。
class Host {
public:
    void open(Gtk::Application& app) {
        auto css = Gtk::CssProvider::create();
        css->load_from_resource("/cn/athena/chinese_chess/ch04ui/style.css");
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        builder_ = Gtk::Builder::create_from_resource("/cn/athena/chinese_chess/ch04ui/window.ui");
        window_ = need<Gtk::ApplicationWindow>("main_window");
        auto* slot = need<Gtk::Box>("board_slot");
        slot->set_overflow(Gtk::Overflow::HIDDEN);
        board_.set_hexpand(true);
        board_.set_vexpand(true);
        slot->append(board_);
        app.add_window(*window_);
        window_->present();
    }

private:
    template <typename T>
    T* need(const char* id) {
        auto* widget = builder_->get_widget<T>(id);
        if (!widget) {
            throw std::runtime_error(std::string("界面里没有 ") + id);
        }
        return widget;
    }

    Glib::RefPtr<Gtk::Builder> builder_;
    Gtk::ApplicationWindow* window_ = nullptr;
    BoardView board_;
};

class ChessApp : public Gtk::Application {
public:
    ChessApp()
        : Gtk::Application("cn.athena.chinese_chess.ch04ui", Gio::Application::Flags::NON_UNIQUE) {}

protected:
    void on_activate() override { host_.open(*this); }

private:
    Host host_;
};

}  // namespace

int main(int argc, char* argv[]) {
    return ChessApp().run(argc, argv);
}
