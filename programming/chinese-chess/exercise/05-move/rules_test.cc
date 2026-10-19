#include "position.hh"

#include <iostream>

namespace {

int failures = 0;

void expect(bool condition, int line) {
    if (!condition) {
        std::cerr << "FAIL line " << line << "\n";
        ++failures;
    }
}

Move find_move(const Position& position, Cell from, Cell to) {
    for (const auto& move : position.legal_moves_from(from)) {
        if (move.to == to) {
            return move;
        }
    }
    expect(false, __LINE__);
    return {};
}

}  // namespace

void check_facing_generals(int& failures) {
    Position position;
    position.turn_ = Side::Red;
    position.board_[0][4] = Piece{Side::Black, Kind::General};
    position.board_[9][4] = Piece{Side::Red, Kind::General};
    auto expect_here = [&](bool condition, int line) {
        if (!condition) {
            std::cerr << "FAIL line " << line << "\n";
            ++failures;
        }
    };
    expect_here(position.in_check(Side::Red), __LINE__);
    expect_here(position.in_check(Side::Black), __LINE__);
    // 照面是攻击，不是着法。帅不能沿空线飞到将的格子上。
    expect_here(!position.is_legal(Cell{4, 9}, Cell{4, 0}), __LINE__);
    // 同一条竖线上再走一步，照面还在，也不能走。
    expect_here(!position.is_legal(Cell{4, 9}, Cell{4, 8}), __LINE__);
    // 横移离开这条竖线，照面解除。
    expect_here(position.is_legal(Cell{4, 9}, Cell{3, 9}), __LINE__);
    expect_here(position.is_legal(Cell{4, 9}, Cell{5, 9}), __LINE__);
}

int main() {
    {
        const auto position = Position::initial();
        expect(position.turn() == Side::Red, __LINE__);
        const Move move = find_move(position, Cell{7, 7}, Cell{4, 7});
        expect(move.notation == "炮二平五", __LINE__);
        if (move.notation != "炮二平五") {
            std::cerr << "  notation was: " << move.notation << "\n";
        }
    }
    {
        auto position = Position::initial();
        position.apply(find_move(position, Cell{7, 7}, Cell{4, 7}));
        expect(position.turn() == Side::Black, __LINE__);
        const Move reply = find_move(position, Cell{7, 0}, Cell{6, 2});
        expect(reply.notation == "马8进7", __LINE__);
        if (reply.notation != "马8进7") {
            std::cerr << "  notation was: " << reply.notation << "\n";
        }
        position.apply(reply);
        expect(position.undo(), __LINE__);
        expect(position.turn() == Side::Black, __LINE__);
        expect(position.at(Cell{7, 0})->kind == Kind::Horse, __LINE__);
    }
    {
        const auto position = Position::initial();
        const auto horse = position.legal_moves_from(Cell{1, 9});
        expect(horse.size() == 2, __LINE__);
        const Move general = find_move(position, Cell{4, 9}, Cell{4, 8});
        expect(general.notation == "帅五进一", __LINE__);
        if (general.notation != "帅五进一") {
            std::cerr << "  notation was: " << general.notation << "\n";
        }
        expect(position.legal_moves_from(Cell{4, 6}).size() == 1, __LINE__);
    }
    {
        auto position = Position::initial();
        const Move advisor = find_move(position, Cell{3, 9}, Cell{4, 8});
        expect(advisor.notation == "仕六进五", __LINE__);
        if (advisor.notation != "仕六进五") {
            std::cerr << "  notation was: " << advisor.notation << "\n";
        }
    }
    check_facing_generals(failures);
    if (failures != 0) {
        std::cerr << failures << " failed\n";
        return 1;
    }
    std::cout << "rules ok\n";
    return 0;
}
