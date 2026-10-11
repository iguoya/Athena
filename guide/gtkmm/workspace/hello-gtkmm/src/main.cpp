// hello-gtkmm —— 工作集模板：最小窗口 + 一个信号连接（C++17 / gtkmm-4.0）
// 想练手就从这里改；要练的 Gtk 部件清单见教程第 4 章起。
#include <gtkmm.h>

class HelloWindow : public Gtk::ApplicationWindow {
public:
  HelloWindow() {
    set_title("hello-gtkmm");
    set_default_size(360, 160);

    button_.set_margin(24);
    // 每次点击重画标签文本：信号处理里改状态，再让部件反映状态
    button_.signal_clicked().connect([this] {
      ++count_;
      button_.set_label("点了我 " + std::to_string(count_) + " 次");
    });
    set_child(button_);
  }

private:
  Gtk::Button button_{"点我"};
  int count_ = 0;
};

int main(int argc, char* argv[]) {
  auto app = Gtk::Application::create("org.athena.workspace.hello-gtkmm");
  return app->make_window_and_run<HelloWindow>(argc, argv);
}
