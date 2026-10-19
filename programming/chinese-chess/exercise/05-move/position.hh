#pragma once

#include <optional>
#include <string>
#include <vector>

// 棋盘坐标按屏幕：x 从左到右 0–8，y 从上到下 0–9。
// y = 0 是黑方底线，y = 9 是红方底线。红方在下，和常见象棋软件一致。
// 红方的「九」在最左（x = 0），「一」在最右（x = 8）。

enum class Side { Red, Black };

enum class Kind { General, Advisor, Elephant, Horse, Rook, Cannon, Pawn };

struct Piece {
    Side side = Side::Red;
    Kind kind = Kind::Pawn;
    bool operator==(const Piece&) const = default;
};

struct Cell {
    int x = 0;
    int y = 0;
    bool operator==(const Cell&) const = default;
};

struct Move {
    Cell from;
    Cell to;
    std::optional<Piece> captured;
    std::string notation;
};

// 局面。BoardView 用 at 画子。Session 用 legal_moves_from 取提示，用 apply / undo 改局面。
// 合法着 = 棋子形状（pseudo_from）再去掉会让己方将被攻击的那些。
class Position {
public:
    static Position initial();

    Side turn() const { return turn_; }
    const std::vector<Move>& history() const { return history_; }
    std::optional<Piece> at(Cell cell) const;

    std::vector<Move> legal_moves_from(Cell from) const;
    bool is_legal(Cell from, Cell to) const;
    void apply(Move move);
    bool undo();

    bool in_check(Side side) const;
    bool has_any_legal_move() const;
    std::string status_text() const;

private:
    // board_[y][x]
    std::optional<Piece> board_[10][9]{};
    Side turn_ = Side::Red;
    std::vector<Move> history_;

    std::vector<Move> pseudo_from(Cell from) const;
    int screens_between(Cell from, Cell target) const;
    bool own_king_safe_after(Cell from, Cell to) const;
    bool attacks(Cell from, Cell target) const;

    // rules_test 要摆一个对局里走不到的局面（将帅已经照面）。窗口不调用。
    friend void check_facing_generals(int& failures);
};
