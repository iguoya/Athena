#ifndef GTKMM_MAINWINDOW_H
#define GTKMM_MAINWINDOW_H

#include <gtkmm/button.h>
#include <gtkmm/window.h>
#include <gtkmm.h>

class MainWindow : public Gtk::Window
{

public:
  MainWindow();
  virtual ~MainWindow();

protected:
  //Signal handlers:
  void on_button_clicked();

  //Member widgets:
  Gtk::Button m_button;
  Fixed fixed;
  ScrolledWindow scrollWindow;
  Label label;
};

#endif // GTKMM_MAINWINDOW_H