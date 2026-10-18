#pragma once

// 这一章的"会话"只有一件事：你点一张贴纸，就圈出它所在角块的三张贴纸，并说出来。

#include "cube.hh"
#include "view.hh"

#include <gtkmm.h>

class Session {
public:
    Session();
    view::NetView& net_view() { return net_view_; }
    void bind(Gtk::Label* info, Gtk::Button* show_sample, Gtk::Button* show_solved);

private:
    void pick(int slot);
    void show(const cube::Stickers& state);

    view::NetView net_view_;
    Gtk::Label* info_ = nullptr;
    cube::Stickers state_ = cube::sample();
};
