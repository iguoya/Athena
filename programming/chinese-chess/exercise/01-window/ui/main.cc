#include <gtkmm.h>

namespace {

// 界面文件版：控件树在 window.blp，颜色在 style.css。
// 这里只负责把程序跑起来，并把这两份文件装进窗口。
class ChessApp : public Gtk::Application {
public:
    ChessApp()
        : Gtk::Application("cn.athena.chinese_chess.ch01ui", Gio::Application::Flags::NON_UNIQUE) {}

protected:
    // 样式和窗口都从资源来。这个函数不创建控件，只把已经描述好的窗口显示出来。
    void on_activate() override {
        auto css = Gtk::CssProvider::create();
        css->load_from_resource("/cn/athena/chinese_chess/ch01ui/style.css");
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        builder_ = Gtk::Builder::create_from_resource("/cn/athena/chinese_chess/ch01ui/window.ui");
        window_ = builder_->get_widget<Gtk::ApplicationWindow>("main_window");
        add_window(*window_);
        window_->present();
    }

private:
    Glib::RefPtr<Gtk::Builder> builder_;
    Gtk::ApplicationWindow* window_ = nullptr;
};

}  // namespace

int main(int argc, char* argv[]) {
    return ChessApp().run(argc, argv);
}
