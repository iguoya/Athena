#pragma once

#include <gtkmm.h>

#include <memory>

using namespace std;

// 静态“关于”对话框的控件树和复用生命周期。窗口只发出 present 请求。
class AboutDialog final {
public:
    explicit AboutDialog(Gtk::Window& parent);

    void present();

private:
    void ensure_created();

    Gtk::Window& m_parent;
    unique_ptr<Gtk::Dialog> m_dialog;
};
