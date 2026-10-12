#include "session.hh"

#include <gtkmm.h>

#include <stdexcept>
#include <string>

namespace {

// 控件从界面文件来。棋盘和规则不在 blp 里：BoardView 放进空位，按钮和标签交给 Session。
class Host {
public:
    void open(Gtk::Application& app) {
        auto css = Gtk::CssProvider::create();
        css->load_from_resource("/cn/athena/chinese_chess/ch05ui/style.css");
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        builder_ = Gtk::Builder::create_from_resource("/cn/athena/chinese_chess/ch05ui/window.ui");
        window_ = need<Gtk::ApplicationWindow>("main_window");
        auto* slot = need<Gtk::Box>("board_slot");
        slot->set_overflow(Gtk::Overflow::HIDDEN);
        slot->append(session_.board());
        session_.bind(*need<Gtk::Label>("status"), *need<Gtk::Label>("black_label"),
                      *need<Gtk::Label>("red_label"), *need<Gtk::TextView>("moves"),
                      *need<Gtk::Button>("new_game"), *need<Gtk::Button>("undo"));
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

    Session session_;
    Glib::RefPtr<Gtk::Builder> builder_;
    Gtk::ApplicationWindow* window_ = nullptr;
};

class ChessApp : public Gtk::Application {
public:
    ChessApp()
        : Gtk::Application("cn.athena.chinese_chess.ch05ui", Gio::Application::Flags::NON_UNIQUE) {}

protected:
    void on_activate() override { host_.open(*this); }

private:
    Host host_;
};

}  // namespace

int main(int argc, char* argv[]) {
    return ChessApp().run(argc, argv);
}
