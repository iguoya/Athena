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
    if (failures != 0) {
        std::cerr << failures << " failed\n";
        return 1;
    }
    std::cout << "rules ok\n";
    return 0;
}
