#include "platform/menu_bar_platform.h"

#include <gtkmm/settings.h>

bool platform_has_native_menu_bar() {
    const auto settings = Gtk::Settings::get_default();
    if (!settings) {
        // 还没有显示后端时保守回答"没有"：窗口里多一条菜单栏，
        // 总比菜单彻底不可达强。
        return false;
    }
    return settings->property_gtk_shell_shows_menubar().get_value();
}
