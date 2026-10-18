#pragma once

// 层先法的三个阶段，写成程序。输入必须是摆正过的状态（DBL 角块在左下后，见 normalize）。
//
//   阶段 1  做第一层：把底层的 3 块（DFR、DLF、DRB）一块一块装回去。
//   阶段 2  翻顶面：让顶层 4 个角块的黄色全朝上。
//   阶段 3  摆顶层：把顶层 4 个角块换到各自的位置。
//
// 每个阶段都有一个能判定的"完成"条件，下一个阶段在不破坏它的前提下推进。

#include "cube.hh"

#include <optional>
#include <string>
#include <vector>

namespace cube {

// 一小段连续的转动，对应讲解里的一句话（"装好这一块""用一次 Sune"）。
struct Segment {
    std::string title;
    std::string note;
    Alg moves;
    std::vector<int> focus;  // 这一段在照看的角块位置，界面用来圈出它们
};

struct Stage {
    std::string title;  // 阶段名
    std::string goal;   // 完成条件，一句话
    std::vector<Segment> segments;
};

struct Plan {
    std::vector<Stage> stages;
    Alg flat() const;          // 全部转动按顺序连起来
    int length() const;
};

// ---- 三个阶段的完成条件 ----
bool layer_done(const Stickers& s);      // DFR、DLF、DRB 都在原位原向（加上永远不动的 DBL）
bool top_oriented(const Stickers& s);    // 顶层 4 个角块的黄色都朝上
// is_solved(s) 是第三个阶段的完成条件。

// 顶层 4 个角块的朝向：0 表示黄色朝上，1、2 表示顺时针拧了几格。位置 URF UFL ULB UBR。
std::array<int, 4> top_twists(const Stickers& s);

// ---- 三个阶段的求解 ----
// 每个函数从 s 出发，返回这个阶段的转动，并把 s 推进到阶段完成之后。
Stage solve_layer(Stickers& s);
Stage solve_orient(Stickers& s);
Stage solve_permute(Stickers& s);

// 三个阶段串起来。s 必须是摆正过的合法状态。
Plan solve(const Stickers& s);

// ---- 讲解里用到的公式 ----
const Alg& sune();
const Alg& antisune();
const Alg& swap_adjacent();
const Alg& swap_diagonal();

}  // namespace cube
