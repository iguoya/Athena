#include <gtkmm.h>

namespace {

// 代码版：同一扇窗，控件在这里用 make_managed 一个个装上去。不读界面文件。
class ChessWindow : public Gtk::ApplicationWindow {
public:
    // 代码版没有 Builder。窗口里有什么，都在这个构造函数里装上。
    ChessWindow() {
        set_title("中国象棋");
        set_default_size(960, 640);

        auto css = Gtk::CssProvider::create();
        css->load_from_string(
            "window { background: #f4ecdf; }"
            "headerbar { background: #7a2e2e; color: white; }"
            "headerbar label { color: white; font-weight: 700; }");
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        auto header = Gtk::make_managed<Gtk::HeaderBar>();
        auto title = Gtk::make_managed<Gtk::Label>("中国象棋");
        header->set_title_widget(*title);
        header->set_show_title_buttons(true);
        set_titlebar(*header);

        auto note = Gtk::make_managed<Gtk::Label>("窗口已经在了。棋盘从下一章开始摆。");
        note->set_margin(24);
        set_child(*note);
    }
};

}  // namespace

int main(int argc, char* argv[]) {
    // 会话总线的名字不能含连字符，所以这里用下划线。标题仍写给人看的「中国象棋」。
    // NON_UNIQUE：教程可以同时开界面文件版和代码版，对照着看。
    auto app = Gtk::Application::create("cn.athena.chinese_chess.ch01",
                                        Gio::Application::Flags::NON_UNIQUE);
    return app->make_window_and_run<ChessWindow>(argc, argv);
}
