#include "session.hh"

#include <sstream>
#include <string>

Session::Session() {
    board_.set_hexpand(true);
    board_.set_vexpand(true);
}

// 界面文件版和代码版都调用这一份。控件由窗口准备好，点选和规则只写在这里。
void Session::bind(Gtk::Label& status, Gtk::Label& black, Gtk::Label& red, Gtk::TextView& moves,
                   Gtk::Button& new_game, Gtk::Button& undo) {
    status_ = &status;
    black_ = &black;
    red_ = &red;
    moves_ = &moves;
    board_.signal_picked().connect(sigc::mem_fun(*this, &Session::on_picked));
    new_game.signal_clicked().connect(sigc::mem_fun(*this, &Session::on_new_game));
    undo.signal_clicked().connect(sigc::mem_fun(*this, &Session::on_undo));
    refresh();
}

// 第二次点在合法落点上就走子。否则点中轮到的一方就改选那一颗，点空处或对方的子就取消。
void Session::on_picked(int x, int y) {
    const Cell cell{x, y};
    if (selected_) {
        for (const auto& move : position_.legal_moves_from(*selected_)) {
            if (move.to == cell) {
                position_.apply(move);
                selected_.reset();
                refresh();
                return;
            }
        }
    }
    const auto piece = position_.at(cell);
    if (piece && piece->side == position_.turn()) {
        selected_ = cell;
    } else {
        selected_.reset();
    }
    refresh();
}

// 回到开局。不在按钮的回调里写规则，只让 Position 换成 initial。
void Session::on_new_game() {
    position_ = Position::initial();
    selected_.reset();
    refresh();
}

// 退回上一步。没有历史时 undo 返回 false，连点不会改局面。
void Session::on_undo() {
    if (position_.undo()) {
        selected_.reset();
        refresh();
    }
}

// 把 Position 的结果摊开：棋盘上的提示、双方得子、棋谱和状态行。绘制不读这些控件。
void Session::refresh() {
    std::vector<Cell> hints;
    if (selected_) {
        for (const auto& move : position_.legal_moves_from(*selected_)) {
            hints.push_back(move.to);
        }
    }
    std::optional<Cell> last_from;
    std::optional<Cell> last_to;
    if (!position_.history().empty()) {
        last_from = position_.history().back().from;
        last_to = position_.history().back().to;
    }
    board_.show_position(position_, selected_, hints, last_from, last_to);

    std::string red_taken;
    std::string black_taken;
    for (const auto& move : position_.history()) {
        if (!move.captured) {
            continue;
        }
        const std::string name = captured_name(*move.captured);
        if (move.captured->side == Side::Red) {
            black_taken += name;
        } else {
            red_taken += name;
        }
    }
    black_->set_text(black_taken.empty() ? "黑方" : "黑方  得子 " + black_taken);
    red_->set_text(red_taken.empty() ? "红方" : "红方  得子 " + red_taken);

    std::ostringstream list;
    int index = 1;
    for (const auto& move : position_.history()) {
        list << index++ << ".  " << move.notation << "\n";
    }
    moves_->get_buffer()->set_text(list.str());
    status_->set_text(position_.status_text());
}

std::string Session::captured_name(Piece piece) {
    if (piece.side == Side::Red) {
        switch (piece.kind) {
        case Kind::General: return "帅";
        case Kind::Advisor: return "仕";
        case Kind::Elephant: return "相";
        case Kind::Horse: return "马";
        case Kind::Rook: return "车";
        case Kind::Cannon: return "炮";
        case Kind::Pawn: return "兵";
        }
    }
    switch (piece.kind) {
    case Kind::General: return "将";
    case Kind::Advisor: return "士";
    case Kind::Elephant: return "象";
    case Kind::Horse: return "马";
    case Kind::Rook: return "车";
    case Kind::Cannon: return "炮";
    case Kind::Pawn: return "卒";
    }
    return "?";
}
