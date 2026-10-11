#pragma once

#include <gtkmm.h>

class Athena : public Gtk::Application {
  protected:
  // 默认 flags 即单实例：第二次启动会转到已运行的实例并触发 on_activate，
  // 由 on_activate 把已有窗口提到前台，不再新开一个进程 / 窗口。
  Athena() : Gtk::Application("cn.yatiger.cpp") {}

  void on_activate() override;

public:
  static Glib::RefPtr<Athena> create() {
    // return Glib::RefPtr<Athena>(new Athena());
    return Glib::make_refptr_for_instance<Athena>(new Athena());
  }
};
