#pragma once

#include <array>
#include <string>

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
// 配色约定：U 白、D 黄、F 绿、B 蓝、L 橙、R 红——魔方圈最通用的西方
// 配色方案（Western/BOY scheme），不是本项目自定的，具体颜色值在
// practice/pocket_cube/view.cc 的 sticker_color() 里。

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

// 穷举下一步的标准非冗余转法集合：2 阶魔方没有固定的中心块参考系，
// 转 D/L/B 的效果都等价于先把整个魔方绕对应轴转半圈、再转 U/R/F，属于
// 冗余操作，穷举时不需要单独列出；只转 U/R/F 三个面、每个面 3 种幅度
// （顺时针/逆时针/180°），3×3 = 9 步就覆盖了全部本质不同的下一步。
//
// 这也是 2 阶魔方速拧圈通用的做法：只转 U/R/F，等价于把 D、L、B 三个
// 面交界处那一个角块固定死当参考——按标准 Western/BOY 配色（U 白、
// D 黄、F 绿、B 蓝、L 橙、R 红），这个角块贴的是黄（D）、橙（L）、
// 蓝（B）三种颜色，坐标是 (x=-1, y=-1, z=-1)。只要应用里从头到尾都只调用
// next_move_set() 给的这 9 种转法（PocketCube::turn() 和这个九宫格
// 都是这样），这个角块自然不会被碰到，不需要另外写代码去“锁定”它。
array<Move, 9> next_move_set();

// 标准转法记号，即 Singmaster notation（辛马斯特记法，David Singmaster
// 在 1980 年代提出，现在是 WCA 世界魔方协会等公认的标准写法）：面字母
// + 幅度后缀——
//   - 单独字母（如 "U"）= 面对这个面看过去顺时针转 90°；
//   - 字母 + '（如 "U'"，读作 "prime"）= 逆时针转 90°；
//   - 字母 + 2（如 "U2"）= 转 180°（顺逆效果一样，不需要区分）。
// 一串转法按顺序空格连写（如 "U U U'"）就是一条完整路径，魔方圈把这
// 叫 algorithm/move sequence，不需要额外的箭头或分隔符。
//
// 例外：R、F 这两个面的顺时针/逆时针文字是互换过的（画面实际观感反
// 馈跟标准计算方向对不上，调的是这里的文字生成，不是 apply_move() 的
// 计算语义——那边的 Turn::Clockwise 对 R/F 依然严格按标准定义，见
// state.cc 的 face_info() 注释）。U/D/L/B 不受影响。
string move_label(Move move);

// move_label() 记号本身 + 括号里的中文注解，比如 "U'（上层 逆时针转
// 90°）"——给不熟悉 Singmaster notation 的新手看，符号和解释同时出现，
// 不需要另外查表。用在九宫格每一格的标注、tooltip，以及
// PocketCube::turn() 的状态提示上，全项目只有这一处生成这句话，不会
// 出现措辞不一致的两份文案。
string move_description(Move move);

// 一次转法对应的目标旋转角度，单位度，标准数学定义（绕
// face_layout(move.face).normal_axis 正方向、右手定则，逆时针为正）：
// 3D 视图把一次离散的状态跳变演示成看得见的转动过程时，用这个角度当
// 动画终点——从 0 渐变到这个值，最后一帧必须正好落在 apply_move() 算
// 出的新坐标上，这也是这个函数存在的意义：动画角度和真实状态跳变共用
// 同一套 direction 计算（见 state.cc apply_move() 的实现），不能各算
// 各的、留下两边不一致的隐患。
double turn_angle_degrees(Move move);

// 3D 视图专用的“转动过程”描述：某一层正在从 0° 转向 turn_angle_
// degrees(move) 的中间状态。current_degrees 应该和目标角度同号，绝对
// 值从 0 渐进到 |目标角度|；动画播完之后调用方要把这个状态清空、改成
// 展示 apply_move() 之后的真实 CubeState——这只是渲染层的过渡效果，
// 不是状态本身的一部分，state.h 其余接口完全不知道动画的存在。
struct TurnAnimation {
    Axis axis;
    int layer_coord;
    double current_degrees;
};

// 2 阶魔方的状态空间数量：8 个角块的排列组合上限是 8!×3^8，但角块
// 朝向总和模 3 必须为 0（这是任意合法转动都保持的不变量），砍掉一个
// 3 的因子，剩 8!×3^7 = 88,179,840——这是 CubeState 这份表示法（标记
// 了魔方在空间中的绝对朝向）能穷举到的具体状态数量。魔方教学资料里
// 最常引用的数字是不计整体朝向的版本：把魔方任意摆放都看成同一个
// 状态，相当于再除以八面体旋转群的阶数 24，得到 7!×3^6 = 3,674,160。
constexpr long long kCubeStateSpaceSize = 88'179'840;
constexpr long long kCubeStateSpaceSizeIgnoringOrientation = 3'674'160;
