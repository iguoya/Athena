#include "menu_bar_platform.h"

// Linux（以及其他未知平台）没有这层系统集成；MainWindow 据此在窗口内
// 显示 Gtk::PopoverMenuBar，绑定同一份 Gtk::Application 菜单模型。
bool platform_has_native_menu_bar() {
    return false;
}
