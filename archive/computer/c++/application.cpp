#include "application.h"

Application::Application()
    : Gtk::Application("cn.yatiger.cpp", Gio::APPLICATION_FLAGS_NONE) {
}


void Application::on_startup()
{
    Gtk::Application::on_startup();
    //    auto builder = Gtk::Builder::create_from_resource("/window.glade");
    builder = Gtk::Builder::create_from_file("window.glade");

    builder->get_widget("window", window);
    window->signal_hide().connect(
                sigc::mem_fun(*this, &Application::on_hide_window)
                );
    cout<<"create window finish..."<<endl;
    add_window(*window);
}

void Application::on_activate() {
    window->present();
}

void Application::on_hide_window() {
    cout << "bye !!!" << endl;
    delete window;
}
