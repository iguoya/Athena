#pragma once

#include "position.hh"

#include <gtkmm.h>

#include <optional>
#include <vector>

// 棋盘和棋子是矢量图，按窗口像素重画。
// on_click 只把像素收成交叉点并发出 signal_picked。走不走得动由 Session 问 Position。
// show_position 记住要画的局面和提示，自己不算合法着。
class BoardView : public Gtk::DrawingArea {
public:
    BoardView();

    void show_position(const Position& position, std::optional<Cell> selected,
                       const std::vector<Cell>& hints, std::optional<Cell> last_from,
                       std::optional<Cell> last_to);

    sigc::signal<void(int, int)>& signal_picked() { return picked_; }

private:
    void draw(const Cairo::RefPtr<Cairo::Context>& context, int width, int height);
    void on_click(int n_press, double x, double y);

    const Position* position_ = nullptr;
    std::optional<Cell> selected_;
    std::vector<Cell> hints_;
    std::optional<Cell> last_from_;
    std::optional<Cell> last_to_;
    sigc::signal<void(int, int)> picked_;
};
