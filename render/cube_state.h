#pragma once

#include <array>

using namespace std;

// 2 阶魔方（Pocket Cube）的状态与转动，不依赖 GTK/Cairo，可以脱离渲染
// 层单独测试。2 阶魔方只有 8 个角块，没有棱块和中心块。
//
// 表示方式：把魔方摆在以自身中心为原点的坐标系里，8 个角块各占据
// (x,y,z) ∈ {-1,1}^3 这 8 个位置之一；每个角块的三个可见贴纸颜色，
// 用“固连在角块本体上、跟着角块一起转”的三个方向标记表示——
// color_x/color_y/color_z 分别是这个角块当前朝 X/Y/Z 轴（具体朝正还是
// 负，由该角块自己的 x/y/z 坐标符号决定）露出的贴纸颜色。
//
// 用户配色约定：F 白、L 橙、U 蓝、R 红、B 黄、D 绿。

enum class Face { U, D, L, R, F, B };

// 一个面最多两种转动幅度：90 度（顺/逆时针）或 180 度。
enum class Turn { Clockwise, CounterClockwise, Half };

struct Move {
    Face face;
    Turn turn;
};

struct Corner {
    int x = 1;
    int y = 1;
    int z = 1;
    Face color_x = Face::R;
    Face color_y = Face::U;
    Face color_z = Face::F;
};

struct CubeState {
    array<Corner, 8> corners;
};

enum class Axis { X, Y, Z };

// 一个面对应的坐标轴信息：法向轴+符号决定“选中哪一层”，u_axis/v_axis
// 是该面内部的两个自由方向——sticker_at() 和渲染层都按这两个轴的符号
// （-1/1）定位面上 2x2 的某一格，两边用的是同一份定义，天然对得上，
// 不需要额外维护一套坐标映射表。
struct FaceLayout {
    Axis normal_axis;
    int normal_sign;
    Axis u_axis;
    Axis v_axis;
};

FaceLayout face_layout(Face face);

// 已复原状态：8 个角块摆在各自“原位”，贴纸颜色跟坐标符号直接对应
// （比如 x=1 的三个角块，它们的 color_x 都是 Face::R）。
CubeState make_solved_cube();

// 应用一次转动，返回转动后的新状态，不修改传入的 state。
CubeState apply_move(const CubeState& state, Move move);

// 是否已复原：每个角块都摆在跟自己初始颜色匹配的坐标位置。
bool is_solved(const CubeState& state);

// 查询某个面上 (u_sign, v_sign) ∈ {-1,1}×{-1,1} 这一格贴纸的颜色；
// u_sign/v_sign 对应 face_layout(face) 里 u_axis/v_axis 的符号。
Face sticker_at(const CubeState& state, Face face, int u_sign, int v_sign);
