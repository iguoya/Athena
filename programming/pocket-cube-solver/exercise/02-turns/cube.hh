#pragma once

// 二阶魔方的状态与转动。不依赖 GTK，可以脱离窗口单独测试。
//
// 状态就是 24 张贴纸各自的颜色。转动不是手写的置换表，而是从 3D 坐标推出来的：
// 把魔方放进 [-2, 2]³ 的盒子，8 个角块各占 (±1, ±1, ±1)，每张贴纸贴在
// 某个角块的某个朝向上。转一个面，就是把这一层的坐标绕轴转 90°。
// 这样转动方向、手性和真实魔方一致，不靠"画面看着对"去调。

#include <array>
#include <cstdint>
#include <random>
#include <string>
#include <string_view>
#include <vector>

namespace cube {

// 六个面，顺序是展开图的 U R F D L B。
enum class Face : std::uint8_t { U, R, F, D, L, B };

constexpr int kFaces = 6;
constexpr int kStickers = 24;
constexpr int kCorners = 8;

// 每格存的是"这张贴纸是哪个面的颜色"。复原态里第 i 格就是 i / 4 号面的颜色。
using Stickers = std::array<std::uint8_t, kStickers>;

Stickers solved();
bool is_solved(const Stickers& s);

// 坐标系：x 向右(R)，y 向上(U)，z 朝向观察者(F)。
struct Vec {
    int x = 0, y = 0, z = 0;
    friend bool operator==(const Vec&, const Vec&) = default;
};

// 一个贴纸位：它所在角块的中心 pos，以及贴纸朝外的方向 normal。
struct Slot {
    Vec pos;
    Vec normal;
};

const Slot& slot(int index);
int slot_index(Vec pos, Vec normal);
Vec face_normal(Face f);
Face face_of_normal(Vec normal);

// 绕 axis 转 turns 个 90°（顺时针从轴的尖端往原点看，turns 可负）。
Vec rotate(Vec v, Vec axis, int turns);

// ---- 转法与记号 ----

// turns 为 1、2、3：顺时针 90°、180°、逆时针 90°。
struct Move {
    Face face;
    int turns;
    friend bool operator==(const Move&, const Move&) = default;
};

using Alg = std::vector<Move>;

Move inverse(Move m);
Alg inverse(const Alg& alg);
std::string to_string(Move m);       // U、U'、U2
std::string to_string(const Alg& alg);
Alg parse(std::string_view text);    // "R U R' U'"；记号不合法抛 std::invalid_argument

Stickers perform(const Stickers& s, Move m);
Stickers perform(const Stickers& s, const Alg& alg);

// 随机转 length 步（只用 U、R、F，相邻两步不转同一个面），给"打乱"按钮用。
Alg random_alg(std::mt19937& rng, int length);

// 只转 U、R、F 就够了：2 阶魔方没有中心块，转 D、L、B 等于整个魔方换个姿势再转
// U、R、F。这 9 种转法下，左下后角块 DBL 永远不动，可以当参照。
const std::array<Move, 9>& basic_moves();

const char* face_letter(Face f);

}  // namespace cube
