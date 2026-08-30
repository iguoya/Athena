#include "athena.h"
#include "mainwindow.h"
#include "menu_bar_platform.h"

void Athena::on_activate() {
  auto builder = Gtk::Builder::create_from_resource("/app/window.ui");
  // auto window = builder->get_widget<MainWindow>("window");
  auto window = Gtk::Builder::get_widget_derived<MainWindow>(builder, "window");
  if (window) {
    add_window(*window);

    // GTK 的 macOS 后端自带一个标准应用菜单模板："关于 / 偏好设置 / 退出"
    // 三项默认置灰，只要应用层按 app.about / app.preferences / app.quit
    // 这三个约定动作名注册，模板会自动接上并变为可用——不需要我们自己
    // 另建一份子菜单，那样反而会在原生菜单栏里变成重复的第二个 "Athena"
    // 菜单（已用真机截图验证过这个重复，不是假设）。其他平台没有这个
    // 模板，MainWindow 自己的菜单模型改为绑给窗口内的 PopoverMenuBar。
    add_action("about", [window]() { window->show_about_dialog(); });
    add_action("preferences", [window]() { window->show_settings_dialog(); });
    add_action("quit", [this]() { quit(); });
    if (!platform_has_native_menu_bar()) {
      set_menubar(window->menu_model());
    }

    window->present();
  }
}