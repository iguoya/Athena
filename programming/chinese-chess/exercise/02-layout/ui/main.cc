#include "wood.hh"

#include <gtkmm.h>

#include <stdexcept>
#include <string>

namespace {

// 界面文件版：window.blp 描述控件树，style.css 上色。
// 木色棋盘是 DrawingArea，界面文件画不了，所以放进名为 board_slot 的空盒子。
class Host {
public:
    // 取出界面文件里的窗口，把画不出来的木色棋盘放进 board_slot。按钮这一章不接信号。
    void open(Gtk::Application& app) {
        auto css = Gtk::CssProvider::create();
        css->load_from_resource("/cn/athena/chinese_chess/ch02ui/style.css");
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        builder_ = Gtk::Builder::create_from_resource("/cn/athena/chinese_chess/ch02ui/window.ui");
        window_ = need<Gtk::ApplicationWindow>("main_window");
        auto* slot = need<Gtk::Box>("board_slot");
        slot->set_overflow(Gtk::Overflow::HIDDEN);
        slot->append(board_);
        app.add_window(*window_);
        window_->present();
    }

private:
    template <typename T>
    // blp 里的 id 是界面和 C++ 的接头。对不上就停，避免静默少一块。
    T* need(const char* id) {
        auto* widget = builder_->get_widget<T>(id);
        if (!widget) {
            throw std::runtime_error(std::string("界面里没有 ") + id);
        }
        return widget;
    }

    Glib::RefPtr<Gtk::Builder> builder_;
    Gtk::ApplicationWindow* window_ = nullptr;
    Wood board_;
};

class ChessApp : public Gtk::Application {
public:
    ChessApp()
        : Gtk::Application("cn.athena.chinese_chess.ch02ui", Gio::Application::Flags::NON_UNIQUE) {}

protected:
    void on_activate() override { host_.open(*this); }

private:
    Host host_;
};

}  // namespace

int main(int argc, char* argv[]) {
    return ChessApp().run(argc, argv);
}
