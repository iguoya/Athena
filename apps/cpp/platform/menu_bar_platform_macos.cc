#include "platform/menu_bar_platform.h"

// GTK 的 macOS 后端会把 Gtk::Application::set_menubar() 的菜单模型接管
// 到系统标准菜单栏，这里不需要任何 Cocoa 调用。
bool platform_has_native_menu_bar() {
    return true;
}
