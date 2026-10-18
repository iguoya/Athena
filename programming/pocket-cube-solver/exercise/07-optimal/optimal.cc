#include "optimal.hh"

#include <stdexcept>

namespace cube {

namespace {

// DBL（位置 6）不动，剩下 7 个位置。排列和朝向都只在这 7 个里数。
constexpr int kMoving[7] = {0, 1, 2, 3, 4, 5, 7};
constexpr int kFactorial[7] = {1, 1, 2, 6, 24, 120, 720};

int slot_of_piece(int piece) {
    for (int i = 0; i < 7; ++i) {
        if (kMoving[i] == piece) {
            return i;
        }
    }
    throw std::logic_error("DBL 不在这张表里");
}

// 每个基本转法对角块的作用，从贴纸版的转动里读出来：把转法作用在复原态上，
// 位置 pos 现在放着哪块、转了几格，就是这个转法在 pos 上的作用。
// 对任意状态：pos 上的新块 = 转之前 from 位置上的块；朝向 = 它原来的朝向 + 这个位置上增加的格数。
const std::array<Cubie, 9>& move_effects() {
    static const auto table = [] {
        std::array<Cubie, 9> t{};
        for (int i = 0; i < 9; ++i) {
            t[i] = cubie_of(cube::perform(solved(), basic_moves()[i]));
        }
        return t;
    }();
    return table;
}

int move_number(Move m) {
    for (int i = 0; i < 9; ++i) {
        if (basic_moves()[i] == m) {
            return i;
        }
    }
    throw std::invalid_argument("最短解只用 U、R、F");
}

}  // namespace

int to_index(const Cubie& c) {
    // 排列：第 i 个位置上放的块，在 7 个块里排第几。Lehmer 码：每一位数"右边比我小的有几个"。
    int perm[7];
    for (int i = 0; i < 7; ++i) {
        perm[i] = slot_of_piece(c.piece[kMoving[i]]);
    }
    int permutation = 0;
    for (int i = 0; i < 7; ++i) {
        int smaller = 0;
        for (int j = i + 1; j < 7; ++j) {
            smaller += perm[j] < perm[i];
        }
        permutation += smaller * kFactorial[6 - i];
    }
    // 朝向：前 6 块当三进制数，最后一块由"总和模 3 为 0"定下来，不必存。
    int twist = 0;
    for (int i = 0; i < 6; ++i) {
        twist = twist * 3 + c.twist[kMoving[i]];
    }
    return permutation * 729 + twist;
}

Cubie from_index(int index) {
    Cubie c{};
    c.piece[kDBL] = kDBL;
    c.twist[kDBL] = 0;
    int twist = index % 729;
    int permutation = index / 729;
    int sum = 0;
    for (int i = 5; i >= 0; --i) {
        c.twist[kMoving[i]] = static_cast<std::uint8_t>(twist % 3);
        sum += twist % 3;
        twist /= 3;
    }
    c.twist[kMoving[6]] = static_cast<std::uint8_t>((3 - sum % 3) % 3);
    // 反过来解 Lehmer 码：第 i 位的数 = 还没用过的块里排第几。
    bool used[7] = {};
    for (int i = 0; i < 7; ++i) {
        int skip = permutation / kFactorial[6 - i];
        permutation %= kFactorial[6 - i];
        for (int k = 0; k < 7; ++k) {
            if (!used[k]) {
                if (skip == 0) {
                    used[k] = true;
                    c.piece[kMoving[i]] = static_cast<std::uint8_t>(kMoving[k]);
                    break;
                }
                --skip;
            }
        }
    }
    return c;
}

Cubie perform(const Cubie& c, Move m) {
    const Cubie& effect = move_effects()[move_number(m)];
    Cubie out{};
    for (int pos = 0; pos < kCorners; ++pos) {
        // effect.piece[pos] 在复原态里就是"来源位置"的编号（复原态里块号等于位置号）。
        const int from = effect.piece[pos];
        out.piece[pos] = c.piece[from];
        out.twist[pos] = static_cast<std::uint8_t>((c.twist[from] + effect.twist[pos]) % 3);
    }
    return out;
}

DistanceTable::DistanceTable() : dist_(kStateCount, 255) {
    // 广度优先：第 d 层的每个状态试 9 种转法，没见过的就是第 d+1 层。
    std::vector<int> frontier = {to_index(cubie_of(solved()))};
    dist_[frontier[0]] = 0;
    histogram_.push_back(1);
    // 转法在角块视角下的作用提前取出来，避免循环里反复查表。
    for (int depth = 1; !frontier.empty(); ++depth) {
        std::vector<int> next;
        for (int index : frontier) {
            const Cubie c = from_index(index);
            for (const Move& m : basic_moves()) {
                const int to = to_index(cube::perform(c, m));
                if (dist_[to] == 255) {
                    dist_[to] = static_cast<std::uint8_t>(depth);
                    next.push_back(to);
                }
            }
        }
        if (!next.empty()) {
            histogram_.push_back(static_cast<long>(next.size()));
        }
        frontier = std::move(next);
    }
}

int DistanceTable::distance(const Stickers& normalized) const {
    return dist_[to_index(cubie_of(normalized))];
}

Alg DistanceTable::solve(const Stickers& normalized) const {
    Cubie c = cubie_of(normalized);
    Alg path;
    for (int d = dist_[to_index(c)]; d > 0; --d) {
        for (const Move& m : basic_moves()) {
            const Cubie next = cube::perform(c, m);
            if (dist_[to_index(next)] == d - 1) {
                path.push_back(m);
                c = next;
                break;
            }
        }
    }
    return path;
}

}  // namespace cube
