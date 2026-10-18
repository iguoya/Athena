#include "cube.hh"

#include <algorithm>
#include <set>
#include <stdexcept>

namespace cube {

namespace {

// ---- 贴纸位的几何 ----

constexpr Vec kNormals[kFaces] = {
    {0, 1, 0},   // U
    {1, 0, 0},   // R
    {0, 0, 1},   // F
    {0, -1, 0},  // D
    {-1, 0, 0},  // L
    {0, 0, -1},  // B
};

// 每个面按"在展开图上从左到右、从上到下"数 4 格。第 r 行第 c 列对应的角块坐标，
// 由这个面在展开图里的摆法决定：U 的上边朝 B，F 的上边朝 U，R 的左边朝 F，
// B 的左边朝 R（从背面看过去），L 的左边朝 B，D 的上边朝 F。
Slot make_slot(int face, int r, int c) {
    const int row_y = r == 0 ? 1 : -1;
    switch (face) {
    case 0: return {{c == 0 ? -1 : 1, 1, r == 0 ? -1 : 1}, kNormals[0]};
    case 1: return {{1, row_y, c == 0 ? 1 : -1}, kNormals[1]};
    case 2: return {{c == 0 ? -1 : 1, row_y, 1}, kNormals[2]};
    case 3: return {{c == 0 ? -1 : 1, -1, r == 0 ? 1 : -1}, kNormals[3]};
    case 4: return {{-1, row_y, c == 0 ? -1 : 1}, kNormals[4]};
    default: return {{c == 0 ? 1 : -1, row_y, -1}, kNormals[5]};
    }
}

const std::array<Slot, kStickers>& slots() {
    static const auto table = [] {
        std::array<Slot, kStickers> t{};
        for (int i = 0; i < kStickers; ++i) {
            t[i] = make_slot(i / 4, (i % 4) / 2, i % 2);
        }
        return t;
    }();
    return table;
}

Vec cross(Vec a, Vec b) {
    return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}
int dot(Vec a, Vec b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
Vec operator*(int k, Vec v) { return {k * v.x, k * v.y, k * v.z}; }
Vec operator+(Vec a, Vec b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
Vec operator-(Vec a) { return {-a.x, -a.y, -a.z}; }

// 从轴的尖端往原点看，顺时针转 90°：v' = a(a·v) - a×v。
Vec rotate_cw(Vec v, Vec a) { return dot(a, v) * a + (-cross(a, v)); }

constexpr int move_index(Move m) { return static_cast<int>(m.face) * 3 + (m.turns - 1); }

// src[m][i]：转完之后第 i 格的颜色来自转之前的哪一格。
using Permutation = std::array<std::uint8_t, kStickers>;

const std::array<Permutation, 18>& permutations() {
    static const auto table = [] {
        std::array<Permutation, 18> t{};
        for (int f = 0; f < kFaces; ++f) {
            for (int turns = 1; turns <= 3; ++turns) {
                Permutation& src = t[f * 3 + turns - 1];
                for (int i = 0; i < kStickers; ++i) {
                    src[i] = static_cast<std::uint8_t>(i);
                }
                const Vec axis = kNormals[f];
                for (int i = 0; i < kStickers; ++i) {
                    const Slot& s = slots()[i];
                    if (dot(s.pos, axis) != 1) {
                        continue;  // 不在被转的这一层
                    }
                    const Vec p = rotate(s.pos, axis, turns);
                    const Vec n = rotate(s.normal, axis, turns);
                    src[slot_index(p, n)] = static_cast<std::uint8_t>(i);
                }
            }
        }
        return t;
    }();
    return table;
}

// ---- 角块位置 ----

constexpr Vec kCornerPos[kCorners] = {
    {1, 1, 1},   {-1, 1, 1},  {-1, 1, -1},  {1, 1, -1},
    {1, -1, 1},  {-1, -1, 1}, {-1, -1, -1}, {1, -1, -1},
};
constexpr const char* kCornerNames[kCorners] = {"URF", "UFL", "ULB", "UBR",
                                                "DFR", "DLF", "DBL", "DRB"};

// 从朝上或朝下的贴纸开始顺时针数。从角块外面看，x→z→y 是顺时针；
// 坐标乘积为负的角块是镜像的，顺序反过来。
const std::array<std::array<int, 3>, kCorners>& corner_table() {
    static const auto table = [] {
        std::array<std::array<int, 3>, kCorners> t{};
        for (int p = 0; p < kCorners; ++p) {
            const Vec pos = kCornerPos[p];
            const Vec ny{0, pos.y, 0};
            const Vec nx{pos.x, 0, 0};
            const Vec nz{0, 0, pos.z};
            const bool mirrored = pos.x * pos.y * pos.z < 0;
            t[p] = {slot_index(pos, ny), slot_index(pos, mirrored ? nz : nx),
                    slot_index(pos, mirrored ? nx : nz)};
        }
        return t;
    }();
    return table;
}

bool top_or_bottom(int color) { return color == 0 || color == 3; }

}  // namespace

Stickers solved() {
    Stickers s{};
    for (int i = 0; i < kStickers; ++i) {
        s[i] = static_cast<std::uint8_t>(i / 4);
    }
    return s;
}

bool is_solved(const Stickers& s) { return s == solved(); }

const Slot& slot(int index) { return slots()[index]; }

int slot_index(Vec pos, Vec normal) {
    for (int i = 0; i < kStickers; ++i) {
        if (slots()[i].pos == pos && slots()[i].normal == normal) {
            return i;
        }
    }
    throw std::logic_error("没有这个贴纸位");
}

Vec face_normal(Face f) { return kNormals[static_cast<int>(f)]; }

Face face_of_normal(Vec normal) {
    for (int f = 0; f < kFaces; ++f) {
        if (kNormals[f] == normal) {
            return static_cast<Face>(f);
        }
    }
    throw std::logic_error("不是面的法向");
}

Vec rotate(Vec v, Vec axis, int turns) {
    const int k = ((turns % 4) + 4) % 4;
    for (int i = 0; i < k; ++i) {
        v = rotate_cw(v, axis);
    }
    return v;
}

// ---- 转法 ----

Move inverse(Move m) { return {m.face, 4 - m.turns}; }

Alg inverse(const Alg& alg) {
    Alg out;
    for (auto it = alg.rbegin(); it != alg.rend(); ++it) {
        out.push_back(inverse(*it));
    }
    return out;
}

const char* face_letter(Face f) {
    static constexpr const char* letters[kFaces] = {"U", "R", "F", "D", "L", "B"};
    return letters[static_cast<int>(f)];
}

std::string to_string(Move m) {
    std::string s = face_letter(m.face);
    if (m.turns == 2) {
        s += '2';
    } else if (m.turns == 3) {
        s += '\'';
    }
    return s;
}

std::string to_string(const Alg& alg) {
    std::string out;
    for (const Move& m : alg) {
        if (!out.empty()) {
            out += ' ';
        }
        out += to_string(m);
    }
    return out;
}

Alg parse(std::string_view text) {
    Alg out;
    std::size_t i = 0;
    while (i < text.size()) {
        const char ch = text[i];
        if (ch == ' ' || ch == '\t' || ch == '\n') {
            ++i;
            continue;
        }
        const std::string_view letters = "URFDLB";
        const auto at = letters.find(ch);
        if (at == std::string_view::npos) {
            throw std::invalid_argument(std::string("不认识的记号：") + ch);
        }
        int turns = 1;
        ++i;
        if (i < text.size() && text[i] == '2') {
            turns = 2;
            ++i;
        } else if (i < text.size() && (text[i] == '\'' || text[i] == '3')) {
            turns = 3;
            ++i;
        }
        out.push_back({static_cast<Face>(at), turns});
    }
    return out;
}

Stickers perform(const Stickers& s, Move m) {
    const Permutation& src = permutations()[move_index(m)];
    Stickers out;
    for (int i = 0; i < kStickers; ++i) {
        out[i] = s[src[i]];
    }
    return out;
}

Stickers perform(const Stickers& s, const Alg& alg) {
    Stickers out = s;
    for (const Move& m : alg) {
        out = perform(out, m);
    }
    return out;
}

Alg random_alg(std::mt19937& rng, int length) {
    Alg out;
    int last_face = -1;
    while (static_cast<int>(out.size()) < length) {
        const Move m = basic_moves()[rng() % 9];
        if (static_cast<int>(m.face) != last_face) {
            out.push_back(m);
            last_face = static_cast<int>(m.face);
        }
    }
    return out;
}

const std::array<Move, 9>& basic_moves() {
    static const std::array<Move, 9> moves = {{
        {Face::U, 1}, {Face::U, 2}, {Face::U, 3},
        {Face::R, 1}, {Face::R, 2}, {Face::R, 3},
        {Face::F, 1}, {Face::F, 2}, {Face::F, 3},
    }};
    return moves;
}

// ---- 角块视角 ----

const char* corner_name(int pos) { return kCornerNames[pos]; }

const std::array<int, 3>& corner_slots(int pos) { return corner_table()[pos]; }

std::array<std::uint8_t, 3> corner_home(int pos) {
    std::array<std::uint8_t, 3> h{};
    for (int j = 0; j < 3; ++j) {
        h[j] = static_cast<std::uint8_t>(corner_slots(pos)[j] / 4);
    }
    return h;
}

bool corner_solved(const Stickers& s, int pos) {
    const auto& sl = corner_slots(pos);
    const auto home = corner_home(pos);
    return s[sl[0]] == home[0] && s[sl[1]] == home[1] && s[sl[2]] == home[2];
}

const char* color_name(int face) {
    static constexpr const char* names[kFaces] = {"黄", "橙", "绿", "白", "红", "蓝"};
    return names[face];
}

namespace {

// 读出某个位置上的角块：返回 (piece, twist)，读不出来返回 {-1, 原因}。
struct Reading {
    int piece = -1;
    int twist = 0;
    std::string why;
};

Reading read_corner(const Stickers& s, int pos) {
    const auto& sl = corner_slots(pos);
    const std::array<int, 3> t = {s[sl[0]], s[sl[1]], s[sl[2]]};
    const std::string shown = std::string(color_name(t[0])) + color_name(t[1]) + color_name(t[2]);
    int k = -1;
    int marks = 0;
    for (int j = 0; j < 3; ++j) {
        if (top_or_bottom(t[j])) {
            k = j;
            ++marks;
        }
    }
    Reading r;
    if (marks != 1) {
        r.why = std::string("位置 ") + corner_name(pos) + " 的三格是「" + shown +
                "」，每个角块必须有且只有一格黄或白";
        return r;
    }
    const std::array<std::uint8_t, 3> rotated = {static_cast<std::uint8_t>(t[k]),
                                                 static_cast<std::uint8_t>(t[(k + 1) % 3]),
                                                 static_cast<std::uint8_t>(t[(k + 2) % 3])};
    for (int q = 0; q < kCorners; ++q) {
        if (corner_home(q) == rotated) {
            r.piece = q;
            r.twist = k;
            return r;
        }
    }
    // 颜色集合对、顺序反了，是镜像角块：真魔方上不存在。
    const std::array<std::uint8_t, 3> flipped = {rotated[0], rotated[2], rotated[1]};
    for (int q = 0; q < kCorners; ++q) {
        if (corner_home(q) == flipped) {
            r.why = std::string("位置 ") + corner_name(pos) + " 的「" + shown +
                    "」顺时针方向反了：真魔方上不存在这样的角块";
            return r;
        }
    }
    r.why = std::string("位置 ") + corner_name(pos) + " 的「" + shown + "」不是任何一个角块的颜色组合";
    return r;
}

}  // namespace

std::string diagnose(const Stickers& s) {
    std::array<int, kFaces> count{};
    for (int i = 0; i < kStickers; ++i) {
        if (s[i] >= kFaces) {
            return "有格子还没涂色";
        }
        ++count[s[i]];
    }
    for (int f = 0; f < kFaces; ++f) {
        if (count[f] != 4) {
            return std::string(color_name(f)) + "色有 " + std::to_string(count[f]) +
                   " 格，应当正好 4 格";
        }
    }
    std::array<bool, kCorners> seen{};
    int twist_sum = 0;
    for (int pos = 0; pos < kCorners; ++pos) {
        const Reading r = read_corner(s, pos);
        if (r.piece < 0) {
            return r.why;
        }
        if (seen[r.piece]) {
            return std::string("角块 ") + corner_name(r.piece) + " 出现了两次";
        }
        seen[r.piece] = true;
        twist_sum += r.twist;
    }
    if (twist_sum % 3 != 0) {
        return "有角块被单独拧过：整体朝向对不上。真魔方转动不会这样，请检查颜色";
    }
    return "";
}

Cubie cubie_of(const Stickers& s) {
    Cubie c{};
    for (int pos = 0; pos < kCorners; ++pos) {
        const Reading r = read_corner(s, pos);
        if (r.piece < 0) {
            throw std::invalid_argument(r.why);
        }
        c.piece[pos] = static_cast<std::uint8_t>(r.piece);
        c.twist[pos] = static_cast<std::uint8_t>(r.twist);
    }
    return c;
}

Stickers stickers_of(const Cubie& c) {
    Stickers s{};
    for (int pos = 0; pos < kCorners; ++pos) {
        const auto home = corner_home(c.piece[pos]);
        const auto& sl = corner_slots(pos);
        for (int j = 0; j < 3; ++j) {
            s[sl[j]] = home[(j - c.twist[pos] + 3) % 3];
        }
    }
    return s;
}

Stickers random_normalized(std::mt19937& rng) {
    std::array<int, kCorners - 1> others = {0, 1, 2, 3, 4, 5, 7};
    std::vector<int> order(others.begin(), others.end());
    std::shuffle(order.begin(), order.end(), rng);
    Cubie c{};
    int sum = 0;
    int next = 0;
    for (int pos = 0; pos < kCorners; ++pos) {
        if (pos == kDBL) {
            c.piece[pos] = kDBL;
            c.twist[pos] = 0;
            continue;
        }
        c.piece[pos] = static_cast<std::uint8_t>(order[next++]);
        // 最后一个位置的朝向由"总和模 3 为 0"定下来，其余随机。
        const bool last = next == kCorners - 1;
        c.twist[pos] = static_cast<std::uint8_t>(last ? (3 - sum % 3) % 3 : rng() % 3);
        sum += c.twist[pos];
    }
    return stickers_of(c);
}

// ---- 摆正姿势 ----

namespace {

// 整个魔方的旋转：三个基向量转到哪里。24 个旋转从两个生成元广度优先得到。
struct Mat {
    Vec ex, ey, ez;
    friend bool operator==(const Mat&, const Mat&) = default;
    Vec operator()(Vec v) const { return v.x * ex + v.y * ey + v.z * ez; }
    Vec transposed(Vec v) const { return {dot(ex, v), dot(ey, v), dot(ez, v)}; }
};

std::vector<Mat> all_rotations() {
    const Mat identity{{1, 0, 0}, {0, 1, 0}, {0, 0, 1}};
    const Vec axes[2] = {{0, 1, 0}, {1, 0, 0}};
    std::vector<Mat> found = {identity};
    for (std::size_t head = 0; head < found.size(); ++head) {
        for (const Vec& a : axes) {
            const Mat& m = found[head];
            const Mat next{rotate_cw(m.ex, a), rotate_cw(m.ey, a), rotate_cw(m.ez, a)};
            if (std::find(found.begin(), found.end(), next) == found.end()) {
                found.push_back(next);
            }
        }
    }
    return found;
}

}  // namespace

Oriented normalize(const Stickers& legal) {
    for (const Mat& g : all_rotations()) {
        Stickers moved{};
        for (int i = 0; i < kStickers; ++i) {
            const Slot& sl = slot(i);
            moved[slot_index(g(sl.pos), g(sl.normal))] = legal[i];
        }
        if (corner_solved(moved, kDBL)) {
            Oriented o;
            o.state = moved;
            for (int f = 0; f < kFaces; ++f) {
                o.input_face[f] = face_of_normal(g.transposed(kNormals[f]));
            }
            return o;
        }
    }
    throw std::invalid_argument("摆正失败：状态不合法");
}

Alg to_input_frame(const Alg& alg, const Oriented& o) {
    Alg out;
    for (const Move& m : alg) {
        out.push_back({o.input_face[static_cast<int>(m.face)], m.turns});
    }
    return out;
}

}  // namespace cube
