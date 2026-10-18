#include "../session.hh"

#include <gtkmm.h>

#include <stdexcept>
#include <string>

namespace {

// 控件从界面文件来。魔方的两个视图是自绘的，放进空位；按钮、输入框和标签交给 Session。
class Host {
public:
    void open(Gtk::Application& app) {
        auto css = Gtk::CssProvider::create();
        css->load_from_resource("/cn/athena/pocket_cube_solver/ch02/style.css");
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        builder_ = Gtk::Builder::create_from_resource("/cn/athena/pocket_cube_solver/ch02/window.ui");
        window_ = need<Gtk::ApplicationWindow>("main_window");
        session_.cube_view().set_hexpand(true);
        session_.cube_view().set_vexpand(true);
        session_.net_view().set_hexpand(true);
        session_.net_view().set_vexpand(true);
        need<Gtk::Box>("cube_slot")->append(session_.cube_view());
        need<Gtk::Box>("net_slot")->append(session_.net_view());

        Widgets w;
        w.status = need<Gtk::Label>("status");
        w.history = need<Gtk::Label>("history");
        w.entry = need<Gtk::Entry>("entry");
        w.run = need<Gtk::Button>("run");
        w.undo = need<Gtk::Button>("undo");
        w.reset = need<Gtk::Button>("reset");
        w.scramble = need<Gtk::Button>("scramble");
        w.speed = need<Gtk::Scale>("speed");
        for (int i = 0; i < 9; ++i) {
            w.turn[i] = need<Gtk::Button>("turn_" + std::to_string(i));
        }
        session_.bind(w);
        app.add_window(*window_);
        window_->present();
    }

private:
    template <typename T>
    T* need(const std::string& id) {
        auto* widget = builder_->get_widget<T>(id);
        if (!widget) {
            throw std::runtime_error("界面里没有 " + id);
        }
        return widget;
    }

    Session session_;
    Glib::RefPtr<Gtk::Builder> builder_;
    Gtk::ApplicationWindow* window_ = nullptr;
};

class CubeApp : public Gtk::Application {
public:
    CubeApp()
        : Gtk::Application("cn.athena.pocket_cube_solver.ch02", Gio::Application::Flags::NON_UNIQUE) {}

protected:
    void on_activate() override { host_.open(*this); }

private:
    Host host_;
};

}  // namespace

int main(int argc, char* argv[]) {
    return CubeApp().run(argc, argv);
}
