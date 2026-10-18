// demo.basics-signals —— 第 3 章「预测–运行」真机演示。
// 两件要亲眼看到的事：同一个 clicked 按连接顺序调用处理器 A、B；
// 窗口从构造到点关闭，信号按什么顺序出现。协议照抄 demos/buttons，
// 这样课程壳能用同一套 JSON-RPC 拉起它。
//
// 自检：./demo-basics-signals --self-check

#include <gtkmm.h>

#include <cstring>
#include <string>

#include "rpc.hpp"

namespace {

class BasicsSignalsDemo : public Gtk::Window {
public:
    BasicsSignalsDemo() {
        set_title("信号时序");
        set_default_size(520, 360);

        // show / map 都是 Run First。show 的默认处理器会先映射窗口，
        // 所以用户处理器看到的顺序是 map，然后才是 show。
        // 两条都要在 show() 之前连上，否则第一次显示已经错过。
        // close-request 返回 bool，connect 的第二个参数没有默认值：
        // false 表示排在默认处理器之前。槽本身再返回 false，默认处理器才会继续关窗。
        signal_show().connect([this] { append("window", "show"); });
        signal_map().connect([this] { append("window", "map"); });
        signal_close_request().connect([this] {
            append("window", "close_request");
            return false;
        }, false);

        box_.set_margin(12);
        box_.set_spacing(8);
        hint_.set_text("先看启动日志，再点一次按钮。");
        hint_.set_halign(Gtk::Align::START);
        button_.set_label("点击我");
        // 普通 connect（不是 connect after）按登记顺序调用，所以先 A 后 B。
        button_.signal_clicked().connect([this] { append("button", "handler", "A"); });
        button_.signal_clicked().connect([this] { append("button", "handler", "B"); });
        log_.set_halign(Gtk::Align::START);
        log_.set_valign(Gtk::Align::START);
        log_.set_wrap(true);
        log_.set_selectable(true);

        box_.append(hint_);
        box_.append(button_);
        box_.append(log_);
        set_child(box_);

        // 「constructed」不是 GTK 信号，标在构造函数末尾，用来和后面的信号对照。
        append("window", "constructed");
    }

    // 由 main 的 signal_activate 处理器在 show() 之前调用。
    void note_activate() { append("window", "activate"); }

private:
    void append(const std::string& widget, const std::string& name,
                const std::string& detail = "") {
        rpc::signal(widget, name, detail);
        ++seq_;
        Glib::ustring line = std::to_string(seq_) + "  " + widget + " " + name;
        if (!detail.empty()) {
            line += " ";
            line += detail;
        }
        if (!lines_.empty()) lines_ += "\n";
        lines_ += line;
        log_.set_text(lines_);
    }

    Gtk::Box box_{Gtk::Orientation::VERTICAL};
    Gtk::Label hint_;
    Gtk::Button button_;
    Gtk::Label log_;
    Glib::ustring lines_;
    int seq_ = 0;
};

}  // namespace

int main(int argc, char* argv[]) {
    bool self_check = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--self-check") == 0) self_check = true;
    }

    auto app = Gtk::Application::create("cn.athena.gtkmm.demo.basics.signals");
    if (self_check) {
        BasicsSignalsDemo window;
        return 0;
    }

    auto window = std::make_shared<BasicsSignalsDemo>();
    app->signal_activate().connect([&app, window] {
        window->note_activate();
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
