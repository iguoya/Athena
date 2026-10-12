#pragma once

#include "board_view.hh"
#include "position.hh"

#include <gtkmm.h>

// 两个窗口共用这一份：局面、点选、记谱、悔棋、新局。
// 按钮和标签由各自的窗口提供。这里把点击接到 Position，再把结果送回 BoardView 和侧栏。
class Session : public sigc::trackable {
public:
    Session();

    BoardView& board() { return board_; }

    void bind(Gtk::Label& status, Gtk::Label& black, Gtk::Label& red, Gtk::TextView& moves,
              Gtk::Button& new_game, Gtk::Button& undo);

private:
    void on_picked(int x, int y);
    void on_new_game();
    void on_undo();
    void refresh();
    static std::string captured_name(Piece piece);

    Position position_ = Position::initial();
    std::optional<Cell> selected_;
    BoardView board_;
    Gtk::Label* status_ = nullptr;
    Gtk::Label* black_ = nullptr;
    Gtk::Label* red_ = nullptr;
    Gtk::TextView* moves_ = nullptr;
};
