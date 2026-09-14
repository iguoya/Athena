#pragma once

// 应用菜单是否已经被系统接管为标准菜单栏：macOS 上 GTK 的 macOS 后端会把
// Gtk::Application::set_menubar() 设置的菜单模型接管到系统标准菜单栏，
// 窗口内没必要再画一条；其他平台没有这层系统集成，菜单模型不会自己出现
// 在任何地方，MainWindow 因此在窗口内嵌入一个 Gtk::PopoverMenuBar，绑定
// 同一份菜单模型才能被用到。各平台实现见 menu_bar_platform_macos.cc /
// menu_bar_platform_other.cc。
bool platform_has_native_menu_bar();
