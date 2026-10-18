#pragma once

// 二阶魔方长什么样：这一章只认识它，不转它。
//
// 2 阶魔方有 6 个面，每个面 2×2 = 4 格，一共 24 张贴纸。
// 它没有中心块、没有棱块，只有 8 个角块；每个角块上有 3 张贴纸。
// 所以 24 = 8 × 3：同一张贴纸既属于某个面，也属于某个角块，这是后面所有章节的出发点。

#include <array>
#include <cstdint>

namespace cube {

constexpr int kStickers = 24;
constexpr int kCorners = 8;

// 每格存一个颜色号。展开图上 6 个面按 U R F D L B 的顺序，每面 4 格，
// 第 i 格属于 i / 4 号面。颜色号和"这个颜色在复原态属于哪个面"相同：
//   0 黄（U 上）  1 橙（R 右）  2 绿（F 前）  3 白（D 下）  4 红（L 左）  5 蓝（B 后）
using Stickers = std::array<std::uint8_t, kStickers>;

const char* color_name(int color);
const char* face_name(int face);

// 复原的魔方：每个面一种颜色。
Stickers solved();

// 一个打乱过的例子（从复原态转了 R U R' U'），用来练习读展开图。
Stickers sample();

// 每个角块上的 3 张贴纸的编号。这张表手抄自展开图：
// 在展开图上数出每个角块的三个格子，从朝上或朝下的那一格开始顺时针记下来。
// 下一章会用 3D 坐标把它自己推出来，这里先当作已知。
const std::array<std::array<int, 3>, kCorners>& corner_slots();
const char* corner_name(int corner);

// 第 slot 号贴纸属于哪个角块。
int corner_of(int slot);

}  // namespace cube
