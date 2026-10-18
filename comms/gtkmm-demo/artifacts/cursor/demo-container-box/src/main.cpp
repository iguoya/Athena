// demo.container-box —— 第 9 章「预测–运行」：水平 Box 里三个按钮的宽度。
// 多余空间先按 hexpand 分成若干档，halign 再决定按钮自己是否填满这一档。
// get_width() 是 size-allocate 交给按钮的内容宽，不含主题内边距；
// 居中时它不跟占位一起变。布局在帧里才落定，拖窗口也没有属性通知，
// 所以 realize 之后用 tick 读，数字没变就不上报。
//
// 自检：./demo-container-box --self-check

#include <gtkmm.h>

#include <cstring>
#include <string>

#include "rpc.hpp"

namespace {

class BoxLayoutDemo : public Gtk::Window {
public:
    BoxLayoutDemo() {
        set_title("盒式布局");
        set_default_size(560, 300);

        root_.set_margin(12);
        root_.set_spacing(10);
        hint_.set_halign(Gtk::Align::START);
        hint_.set_wrap(true);
        hint_.set_text("标签是三个按钮的 get_width()。先预测，再改开关或拉宽窗口。");

        // 垂直盒在横向上把子部件拉到同一宽度；行保持默认 FILL，窗口变宽才进得来。
        row_.set_hexpand(true);
        a_.set_label("甲");
        b_.set_label("乙");
        c_.set_label("丙");
        row_.append(a_);
        row_.append(b_);
        row_.append(c_);

        // 甲的开关用来看「两个都 hexpand」：任务里的三个预测点都要在界面上摆得出来。
        a_exp_.set_label("甲 hexpand");
        b_exp_.set_label("乙 hexpand");
        b_center_.set_label("乙居中");
        gap_.set_label("间距 16");
        toggles_.set_spacing(12);
        for (Gtk::CheckButton* toggle : {&a_exp_, &b_exp_, &b_center_, &gap_}) {
            toggle->signal_toggled().connect([this] { apply(); });
            toggles_.append(*toggle);
        }

        readout_.set_halign(Gtk::Align::START);
        readout_.set_selectable(true);
        readout_.set_text("a=…;b=…;c=…");

        root_.append(hint_);
        root_.append(row_);
        root_.append(toggles_);
        root_.append(readout_);
        set_child(root_);

        signal_realize().connect([this] {
            add_tick_callback([this](const Glib::RefPtr<Gdk::FrameClock>&) {
                publish();
                return true;
            });
        });
    }

private:
    void apply() {
        a_.set_hexpand(a_exp_.get_active());
        b_.set_hexpand(b_exp_.get_active());
        // 关掉「乙居中」要回到默认 FILL，否则按钮会停在上一次的对齐。
        b_.set_halign(b_center_.get_active() ? Gtk::Align::CENTER : Gtk::Align::FILL);
        row_.set_spacing(gap_.get_active() ? 16 : 0);
    }

    void publish() {
        const int aw = a_.get_width();
        const int bw = b_.get_width();
        const int cw = c_.get_width();
        // 第一帧分配还没做完，get_width() 是 0。
        if (aw <= 0 || bw <= 0 || cw <= 0) return;
        const std::string detail = "a=" + std::to_string(aw) + ";b=" + std::to_string(bw) +
                                   ";c=" + std::to_string(cw);
        if (detail == last_) return;
        last_ = detail;
        rpc::signal("layout", "widths", detail);
        readout_.set_text(detail);
    }

    Gtk::Box root_{Gtk::Orientation::VERTICAL};
    Gtk::Label hint_;
    Gtk::Box row_{Gtk::Orientation::HORIZONTAL};
    Gtk::Button a_;
    Gtk::Button b_;
    Gtk::Button c_;
    Gtk::Box toggles_{Gtk::Orientation::HORIZONTAL};
    Gtk::CheckButton a_exp_;
    Gtk::CheckButton b_exp_;
    Gtk::CheckButton b_center_;
    Gtk::CheckButton gap_;
    Gtk::Label readout_;
    std::string last_;
};

}  // namespace

int main(int argc, char* argv[]) {
    bool self_check = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--self-check") == 0) self_check = true;
    }

    auto app = Gtk::Application::create("cn.athena.gtkmm.demo.container.box");
    if (self_check) {
        BoxLayoutDemo window;
        return 0;
    }

    auto window = std::make_shared<BoxLayoutDemo>();
    app->signal_activate().connect([&app, window] {
        window->set_application(app);
        window->show();
        rpc::notify("ready", "{\"protocol_version\": 1}");
        rpc::watch_requests([&app](const std::string& id, const std::string& method) {
            if (method == "initialize") {
                rpc::respond(id, "{\"protocol_version\": 1}");
            } else if (method == "ping") {
                rpc::respond(id, "\"pong\"");
            } else if (method == "shutdown") {
                app->quit();
            }
        });
    });
    // 自定义参数已自行解析；传空参避免 GApplication 把未知选项当成错误。
    return app->run(0, nullptr);
}
