#include "position.hh"

#include <algorithm>
#include <cstdlib>
#include <utility>

namespace {

bool on_board(int x, int y) {
    return x >= 0 && x < 9 && y >= 0 && y < 10;
}

Side opposite(Side side) {
    return side == Side::Red ? Side::Black : Side::Red;
}

bool in_palace(Side side, Cell cell) {
    if (cell.x < 3 || cell.x > 5) {
        return false;
    }
    if (side == Side::Red) {
        return cell.y >= 7 && cell.y <= 9;
    }
    return cell.y >= 0 && cell.y <= 2;
}

bool on_own_half(Side side, int y) {
    return side == Side::Red ? y >= 5 : y <= 4;
}

// 下面四个只给 legal_moves_from 写棋谱：子名、路名、步数，以及这一步算不算前进。
const char* piece_name(Piece piece) {
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

std::string file_token(Side side, int x) {
    if (side == Side::Black) {
        return std::to_string(x + 1);
    }
    static const char* red[] = {"九", "八", "七", "六", "五", "四", "三", "二", "一"};
    return red[x];
}

std::string count_token(Side side, int n) {
    if (side == Side::Black) {
        return std::to_string(n);
    }
    static const char* red[] = {"", "一", "二", "三", "四", "五", "六", "七", "八", "九"};
    return red[n];
}

bool is_forward(Side side, int from_y, int to_y) {
    return side == Side::Red ? to_y < from_y : to_y > from_y;
}

}  // namespace

std::optional<Piece> Position::at(Cell cell) const {
    if (!on_board(cell.x, cell.y)) {
        return std::nullopt;
    }
    return board_[cell.y][cell.x];
}

// 开局。y = 0 是黑方底线，y = 9 是红方底线。红方先走。
Position Position::initial() {
    Position position;
    const Kind back[] = {
        Kind::Rook, Kind::Horse, Kind::Elephant, Kind::Advisor, Kind::General,
        Kind::Advisor, Kind::Elephant, Kind::Horse, Kind::Rook,
    };
    for (int x = 0; x < 9; ++x) {
        position.board_[0][x] = Piece{Side::Black, back[x]};
        position.board_[9][x] = Piece{Side::Red, back[x]};
    }
    position.board_[2][1] = Piece{Side::Black, Kind::Cannon};
    position.board_[2][7] = Piece{Side::Black, Kind::Cannon};
    position.board_[7][1] = Piece{Side::Red, Kind::Cannon};
    position.board_[7][7] = Piece{Side::Red, Kind::Cannon};
    for (int x = 0; x < 9; x += 2) {
        position.board_[3][x] = Piece{Side::Black, Kind::Pawn};
        position.board_[6][x] = Piece{Side::Red, Kind::Pawn};
    }
    return position;
}

// 按吃子的几何判断 from 上的子能不能打到 target。将军检测走这里。
// 炮在这里要求中间恰好一个子。炮走到空位不是吃子，由 pseudo_from 另判「中间没有子」。
bool Position::attacks(Cell from, Cell target) const {
    const auto piece = at(from);
    if (!piece || !on_board(target.x, target.y) || from == target) {
        return false;
    }
    const int dx = target.x - from.x;
    const int dy = target.y - from.y;
    const int adx = std::abs(dx);
    const int ady = std::abs(dy);

    auto between = [&]() {
        if (dx != 0 && dy != 0) {
            return -1;
        }
        const int step_x = (dx > 0) - (dx < 0);
        const int step_y = (dy > 0) - (dy < 0);
        int count = 0;
        int x = from.x + step_x;
        int y = from.y + step_y;
        while (x != target.x || y != target.y) {
            if (board_[y][x]) {
                ++count;
            }
            x += step_x;
            y += step_y;
        }
        return count;
    };

    switch (piece->kind) {
    case Kind::General:
        if (adx + ady == 1 && in_palace(piece->side, target)) {
            return true;
        }
        // 将帅照面：同一条竖线、中间没有子，双方将帅互相攻击。
        if (dx == 0 && at(target) && at(target)->kind == Kind::General && between() == 0) {
            return true;
        }
        return false;
    case Kind::Advisor:
        return adx == 1 && ady == 1 && in_palace(piece->side, from) && in_palace(piece->side, target);
    case Kind::Elephant:
        if (adx != 2 || ady != 2 || !on_own_half(piece->side, target.y)) {
            return false;
        }
        return !at(Cell{from.x + dx / 2, from.y + dy / 2});
    case Kind::Horse:
        if (!((adx == 1 && ady == 2) || (adx == 2 && ady == 1))) {
            return false;
        }
        if (adx == 2) {
            return !at(Cell{from.x + dx / 2, from.y});
        }
        return !at(Cell{from.x, from.y + dy / 2});
    case Kind::Rook:
        return between() == 0;
    case Kind::Cannon:
        return between() == 1;
    case Kind::Pawn:
        if (piece->side == Side::Red) {
            if (dx == 0 && dy == -1) {
                return true;
            }
            return from.y <= 4 && adx == 1 && dy == 0;
        }
        if (dx == 0 && dy == 1) {
            return true;
        }
        return from.y >= 5 && adx == 1 && dy == 0;
    }
    return false;
}

// 找到这一方的将或帅，看对方有没有一子 attacks 到那一格。
bool Position::in_check(Side side) const {
    Cell king{-1, -1};
    for (int y = 0; y < 10; ++y) {
        for (int x = 0; x < 9; ++x) {
            const auto piece = board_[y][x];
            if (piece && piece->side == side && piece->kind == Kind::General) {
                king = Cell{x, y};
            }
        }
    }
    if (king.x < 0) {
        return false;
    }
    for (int y = 0; y < 10; ++y) {
        for (int x = 0; x < 9; ++x) {
            const auto piece = board_[y][x];
            if (piece && piece->side != side && attacks(Cell{x, y}, king)) {
                return true;
            }
        }
    }
    return false;
}

// 同一条直线上、两端之间的子数。不在一条直线上返回 -1。车、炮和将帅照面都用这个数。
int Position::screens_between(Cell from, Cell target) const {
    if (from.x != target.x && from.y != target.y) {
        return -1;
    }
    const int step_x = (target.x > from.x) - (target.x < from.x);
    const int step_y = (target.y > from.y) - (target.y < from.y);
    int count = 0;
    int x = from.x + step_x;
    int y = from.y + step_y;
    while (x != target.x || y != target.y) {
        if (board_[y][x]) {
            ++count;
        }
        x += step_x;
        y += step_y;
    }
    return count;
}

// 只生成形状上走得到的格，不看走完之后自己的将被攻击，也不写棋谱。
std::vector<Move> Position::pseudo_from(Cell from) const {
    std::vector<Move> moves;
    const auto piece = at(from);
    if (!piece) {
        return moves;
    }

    auto land = [&](int x, int y) {
        if (!on_board(x, y)) {
            return;
        }
        const Cell target{x, y};
        const auto occupant = board_[y][x];
        if (occupant && occupant->side == piece->side) {
            return;
        }
        bool ok = false;
        // 车、炮走到空位要中间没有子。吃子（炮还要恰好一个炮架）交给 attacks。
        if (piece->kind == Kind::Cannon && !occupant) {
            ok = screens_between(from, target) == 0;
        } else if (piece->kind == Kind::Rook && !occupant) {
            ok = screens_between(from, target) == 0;
        } else {
            ok = attacks(from, target);
        }
        if (ok) {
            moves.push_back(Move{from, target, occupant, {}});
        }
    };

    switch (piece->kind) {
    case Kind::Rook:
    case Kind::Cannon:
        for (const auto [dx, dy] : {std::pair{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
            for (int step = 1; step < 10; ++step) {
                const int x = from.x + dx * step;
                const int y = from.y + dy * step;
                if (!on_board(x, y)) {
                    break;
                }
                land(x, y);
                if (board_[y][x] && piece->kind == Kind::Rook) {
                    break;
                }
            }
        }
        break;
    default:
        for (int y = 0; y < 10; ++y) {
            for (int x = 0; x < 9; ++x) {
                land(x, y);
            }
        }
        break;
    }
    return moves;
}

// 在副本上试走，不改当前局面。in_check 用 attacks，所以炮隔一子照将也会被算进去。
bool Position::own_king_safe_after(Cell from, Cell to) const {
    const auto moving = at(from);
    if (!moving) {
        return false;
    }
    Position next = *this;
    next.board_[to.y][to.x] = moving;
    next.board_[from.y][from.x] = std::nullopt;
    return !next.in_check(moving->side);
}

// 给 Session 的入口。不是当前走棋方就返回空。先取伪着，丢掉将军自己的，再写成棋谱。
std::vector<Move> Position::legal_moves_from(Cell from) const {
    const auto piece = at(from);
    if (!piece || piece->side != turn_) {
        return {};
    }
    std::vector<Cell> same_file;
    for (int y = 0; y < 10; ++y) {
        const auto other = board_[y][from.x];
        if (other && *other == *piece) {
            same_file.push_back(Cell{from.x, y});
        }
    }
    std::sort(same_file.begin(), same_file.end(), [&](Cell a, Cell b) {
        return is_forward(piece->side, b.y, a.y);
    });

    std::string prefix = piece_name(*piece);
    if (same_file.size() == 2) {
        prefix = (same_file.front() == from ? "前" : "后") + prefix;
    } else if (same_file.size() == 3) {
        const char* rank[] = {"前", "中", "后"};
        for (int i = 0; i < 3; ++i) {
            if (same_file[static_cast<size_t>(i)] == from) {
                prefix = std::string(rank[i]) + prefix;
            }
        }
    } else if (same_file.size() > 3) {
        const int index = static_cast<int>(
            std::find(same_file.begin(), same_file.end(), from) - same_file.begin());
        const char* rank[] = {"前", "二", "三", "四", "后"};
        const int label = index == static_cast<int>(same_file.size()) - 1 ? 4 : index;
        prefix = std::string(rank[label]) + prefix;
    } else {
        prefix += file_token(piece->side, from.x);
    }

    std::vector<Move> legal;
    for (auto move : pseudo_from(from)) {
        if (!own_king_safe_after(from, move.to)) {
            continue;
        }
        std::string action;
        if (move.to.y == from.y) {
            action = "平" + file_token(piece->side, move.to.x);
        } else {
            const bool forward = is_forward(piece->side, from.y, move.to.y);
            action = forward ? "进" : "退";
            const bool to_file = piece->kind == Kind::Horse || piece->kind == Kind::Elephant ||
                                 piece->kind == Kind::Advisor;
            if (to_file) {
                action += file_token(piece->side, move.to.x);
            } else {
                action += count_token(piece->side, std::abs(move.to.y - from.y));
            }
        }
        move.notation = prefix + action;
        legal.push_back(std::move(move));
    }
    return legal;
}

bool Position::is_legal(Cell from, Cell to) const {
    for (const auto& move : legal_moves_from(from)) {
        if (move.to == to) {
            return true;
        }
    }
    return false;
}

// 落子、记下被吃的子、交换走棋方。棋谱字符串在送进来之前已经写好。
void Position::apply(Move move) {
    move.captured = board_[move.to.y][move.to.x];
    board_[move.to.y][move.to.x] = board_[move.from.y][move.from.x];
    board_[move.from.y][move.from.x] = std::nullopt;
    turn_ = opposite(turn_);
    history_.push_back(std::move(move));
}

// 用历史里记下的被吃子放回去。没有历史就返回 false。
bool Position::undo() {
    if (history_.empty()) {
        return false;
    }
    const Move move = history_.back();
    history_.pop_back();
    board_[move.from.y][move.from.x] = board_[move.to.y][move.to.x];
    board_[move.to.y][move.to.x] = move.captured;
    turn_ = opposite(turn_);
    return true;
}

// 给 status_text 用。当前不该走的一方，legal_moves_from 本来就是空的。
bool Position::has_any_legal_move() const {
    for (int y = 0; y < 10; ++y) {
        for (int x = 0; x < 9; ++x) {
            if (!legal_moves_from(Cell{x, y}).empty()) {
                return true;
            }
        }
    }
    return false;
}

// 先看有没有合法着，再看有没有被将军。无着且被将军是将死，无着且未被将军是困毙。
std::string Position::status_text() const {
    const bool check = in_check(turn_);
    const bool any = has_any_legal_move();
    const bool red = turn_ == Side::Red;
    if (!any && check) {
        return red ? "黑胜 · 红方被将死" : "红胜 · 黑方被将死";
    }
    if (!any) {
        return red ? "黑胜 · 红方困毙" : "红胜 · 黑方困毙";
    }
    if (check) {
        return red ? "将军 · 轮到红方" : "将军 · 轮到黑方";
    }
    return red ? "轮到红方" : "轮到黑方";
}
