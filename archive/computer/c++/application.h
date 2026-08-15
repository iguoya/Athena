#ifndef Application_H
#define Application_H

#include <gtkmm.h>
#include <giomm.h>
#include "assert.h"
#include "menumodel.h"
#include <iostream>
#include "factory.h"
#include "product.h"
using namespace std;
using namespace Glib;

class Application : public Gtk::Application
{
public:
    Application();

protected:
    void on_startup() override;
    void on_activate() override;

private:
    RefPtr<Gtk::Builder> builder;
    Gtk::Window* window;
    void on_hide_window();
};


//#include <gtkmm/application.h>
//#include <glibmm/refptr.h>
//#include <giomm/settings.h>
//#include "mainwindow.h"

//class Application : public Gtk::Application
//{
//public:
////    Application();

//    static Glib::RefPtr<Application> create();

//protected:
//    Application();

//    void on_activate() override;

//private:
//    MainWindow* create_window();
//    void on_hide_window(Gtk::Window* window);
//};

#endif // Application_H
