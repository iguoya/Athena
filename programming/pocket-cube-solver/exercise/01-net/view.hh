#pragma once

// 自绘的展开图 NetView。它只画 Session 交给它的状态，不保存魔方。

#include "cube.hh"

#include <gtkmm.h>

#include <array>

namespace view {

// 被圈出来的贴纸位。Session 用它指出"你点的这张贴纸所在的角块"。
using Marks = std::array<bool, cube::kStickers>;

// 展开图。点击某一格时发出信号。
class NetView : public Gtk::DrawingArea {
public:
    NetView();
    void show(const cube::Stickers& state, const Marks& marks);
    sigc::signal<void(int)>& signal_picked() { return picked_; }

private:
    void draw(const Cairo::RefPtr<Cairo::Context>& cr, int width, int height);
    void on_click(int n_press, double x, double y);

    cube::Stickers state_ = cube::solved();
    Marks marks_{};
    sigc::signal<void(int)> picked_;
};

// 面号 0..5 的颜色，其它值（没涂）是灰。
std::array<double, 3> rgb(int face);

}  // namespace view
