#include "../session.hh"

#include <gtkmm.h>

#include <stdexcept>
#include <string>

namespace {

// 控件从界面文件来。魔方的两个视图是自绘的，放进空位；按钮和标签交给 Session。
class Host {
public:
    void open(Gtk::Application& app) {
        auto css = Gtk::CssProvider::create();
        css->load_from_resource("/cn/athena/pocket_cube_solver/ch04/style.css");
        Gtk::StyleContext::add_provider_for_display(
            Gdk::Display::get_default(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

        builder_ = Gtk::Builder::create_from_resource("/cn/athena/pocket_cube_solver/ch04/window.ui");
        window_ = need<Gtk::ApplicationWindow>("main_window");
        need<Gtk::Box>("cube_slot")->append(session_.cube_view());
        need<Gtk::Box>("net_slot")->append(session_.net_view());
        session_.cube_view().set_hexpand(true);
        session_.cube_view().set_vexpand(true);
        session_.net_view().set_hexpand(true);
        session_.net_view().set_vexpand(true);

        Widgets w;
        w.status = need<Gtk::Label>("status");
        w.note = need<Gtk::Label>("note");
        w.moves = need<Gtk::Label>("moves");
        w.stage = {need<Gtk::Label>("stage_1"), need<Gtk::Label>("stage_2")};
        w.scramble = need<Gtk::Button>("scramble");
        w.reset = need<Gtk::Button>("reset");
        w.solve = need<Gtk::Button>("solve");
        w.prev = need<Gtk::Button>("prev");
        w.play = need<Gtk::Button>("play");
        w.next = need<Gtk::Button>("next");
        w.speed = need<Gtk::Scale>("speed");
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
        : Gtk::Application("cn.athena.pocket_cube_solver.ch04", Gio::Application::Flags::NON_UNIQUE) {}

protected:
    void on_activate() override { host_.open(*this); }

private:
    Host host_;
};

}  // namespace

int main(int argc, char* argv[]) {
    return CubeApp().run(argc, argv);
}
