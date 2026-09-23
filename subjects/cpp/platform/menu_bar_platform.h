#pragma once

// 系统是否把应用菜单接管成全局菜单栏。
//
// 这不是平台问题，是桌面环境的能力问题：macOS 的 GTK 后端会把
// Gtk::Application::set_menubar() 的菜单模型接管到系统菜单栏，Unity、
// 某些 KDE 配置也会；普通的 GNOME / Windows 不会，窗口里得自己画一条。
//
// GTK 早就把这件事抽象成了设置项 gtk-shell-shows-menubar，运行时问它即可，
// 不需要按平台编译不同实现（ADR 0047）。
bool platform_has_native_menu_bar();
