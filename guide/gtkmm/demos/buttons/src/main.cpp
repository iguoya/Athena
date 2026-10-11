// demo.buttons —— 「按钮」章的真机演示（应用 ADR 0001、0002）。
// 具象化三个理论点：Gtk::Button 的 clicked、Gtk::ToggleButton 的 toggled、
// Gtk::CheckButton 的活跃状态。每个信号都通过 rpc::signal 上报给课程壳。
//
// 运行方式：由课程壳 spawn 并通过 stdio 说 JSON-RPC；也可独立运行
//   ./demo-buttons --demo-id demo.buttons
// 自检：./demo-buttons --self-check   （构造界面后即退出 0，供 check.py 全量验证）

#include <gtkmm.h>

#include <cstring>
#include <iostream>

#include "rpc.hpp"

namespace {

class ButtonsDemo : public Gtk::Window {
public:
    ButtonsDemo() {
        set_title("Buttons 演示");
        set_default_size(420, 220);

        set_child(grid_);
        grid_.set_margin(12);
        grid_.set_row_spacing(10);
        grid_.set_column_spacing(10);

        button_.set_label("点击我（_C）");
        button_.set_use_underline(true);
        button_.signal_clicked().connect([this] {
            rpc::signal("button", "clicked");
            status_.set_text("clicked 信号已发出");
        });
        grid_.attach(button_, 0, 0);

        toggle_.set_label("切换我");
        toggle_.signal_toggled().connect([this] {
            const auto active = toggle_.get_active();
            rpc::signal("toggle", "toggled", active ? "active" : "inactive");
            status_.set_text(Glib::ustring::compose(
                "toggled：get_active() = %1", active ? "true" : "false"));
        });
        grid_.attach(toggle_, 0, 1);

        check_.set_label("勾选我");
        check_.signal_toggled().connect([this] {
            const auto active = check_.get_active();
            rpc::signal("check", "toggled", active ? "active" : "inactive");
            status_.set_text(Glib::ustring::compose(
                "CheckButton：get_active() = %1", active ? "true" : "false"));
        });
        grid_.attach(check_, 0, 2);

        status_.set_halign(Gtk::Align::START);
        grid_.attach(status_, 1, 0, 1, 3);
    }

private:
    Gtk::Grid grid_;
    Gtk::Button button_;
    Gtk::ToggleButton toggle_;
    Gtk::CheckButton check_;
    Gtk::Label status_;
};

}  // namespace

int main(int argc, char* argv[]) {
    bool self_check = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--self-check") == 0) self_check = true;
    }

    auto app = Gtk::Application::create("cn.athena.gtkmm.demo.buttons");
    if (self_check) {
        // 自检只构造控件树、连接信号，不进主循环：证明代码可加载、窗口可建。
        ButtonsDemo window;
        return 0;
    }

    auto window = std::make_shared<ButtonsDemo>();
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
    // 自定义参数（--demo-id 等）已自行解析；传空参避免 GApplication 当未知选项拒绝。
    return app->run(0, nullptr);
}
