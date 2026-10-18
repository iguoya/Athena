#include "cube.hh"

#include <algorithm>
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

}  // namespace cube
