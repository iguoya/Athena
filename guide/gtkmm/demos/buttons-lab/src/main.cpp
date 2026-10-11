// exp.buttons —— 骨架实验：把 demo.buttons 里观察到的信号写进自己的程序。
// 骨架不改一行也能编译运行（ADR 0059）；学习者只改标了 TODO 的区域。
//
// 编译运行（MSYS2 / Homebrew / Linux 均为同一套）：
//   cmake -S demos -B build-native && cmake --build build-native --target exp-buttons
//   ./build-native/exp-buttons
//
// 跑通标准（acceptance）：
//   1. 程序启动显示一个按钮，初始文案是「还没连信号」；
//   2. 补全 TODO 后，点击按钮文案变为「clicked 信号收到！」；
//   3. 再点一次，文案变为「clicked 信号收到 2 次」。

#include <gtkmm.h>

#include <cstring>
#include <memory>

namespace {

class SignalLab : public Gtk::Window {
public:
    SignalLab() {
        set_title("exp.buttons：第一次连接信号");
        set_default_size(420, 160);

        set_child(box_);
        box_.set_margin(12);
        box_.set_spacing(10);

        button_.set_label("点我");
        box_.append(button_);

        status_.set_text("还没连信号");
        status_.set_halign(Gtk::Align::START);
        box_.append(status_);

        // —— 以下驱动请勿改（除非题目要求）——
        // 学员任务：连接 button_ 的 clicked 信号。每次点击后 status_ 依次显示
        // 「clicked 信号收到！」「clicked 信号收到 2 次」「clicked 信号收到 3 次」……
        // 提示：连接写在下面的 TODO 区域；点击次数自己维护一个计数器。
        //
        // TODO(学员)：在这里连接信号（约 4 行）

        // —— 以上驱动请勿改 ——
    }

private:
    Gtk::Box box_{Gtk::Orientation::VERTICAL};
    Gtk::Button button_;
    Gtk::Label status_;
};

}  // namespace

int main(int argc, char* argv[]) {
    bool self_check = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--self-check") == 0) self_check = true;
    }
    auto app = Gtk::Application::create("cn.athena.gtkmm.exp.buttons");
    if (self_check) {
        // 自检只构造控件树，不进主循环：证明骨架可编译、可加载（ADR 0059）。
        SignalLab window;
        return 0;
    }
    return app->make_window_and_run<SignalLab>(argc, argv);
}
