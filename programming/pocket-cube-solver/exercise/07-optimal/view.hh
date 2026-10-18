#pragma once

// 两个自绘控件：展开图 NetView 和立体图 CubeView。
// 它们只画 Session 交给它们的状态，不保存魔方，也不知道求解和阶段。

#include "cube.hh"

#include <gtkmm.h>

#include <array>
#include <optional>

namespace view {

// 贴纸位被圈出来的标记。Session 用它指出"这一步在动哪几格"。
using Marks = std::array<bool, cube::kStickers>;

// 展开图。点击某一格时发出信号（涂色模式用）。
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

// 立体图。一次转动的动画不是状态的一部分：Session 在转动之前的状态上，
// 给出"哪一层转到哪一刻"，动画放完再把转完的状态交给 show。
class CubeView : public Gtk::DrawingArea {
public:
    CubeView();
    void show(const cube::Stickers& state, const Marks& marks);
    // progress 0 到 1：move 这一层从原位转到转完。
    void show_turning(const cube::Stickers& before, cube::Move move, double progress);

private:
    void draw(const Cairo::RefPtr<Cairo::Context>& cr, int width, int height);

    cube::Stickers state_ = cube::solved();
    Marks marks_{};
    std::optional<cube::Move> turning_;
    double progress_ = 0.0;
    double yaw_ = 0.62;    // 从前右上方看过去，正好看见 U、F、R 三个面
    double pitch_ = 0.5;
    double drag_yaw_ = 0.0;
    double drag_pitch_ = 0.0;
};

// 面号 0..5 的颜色，其它值（没涂）是灰。
std::array<double, 3> rgb(int face);

}  // namespace view
