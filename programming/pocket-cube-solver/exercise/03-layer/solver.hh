#pragma once

// 层先法的三个阶段，写成程序。输入必须是摆正过的状态（DBL 角块在左下后）。
//
//   阶段 1  做第一层：把底层的 3 块（DFR、DLF、DRB）一块一块装回去。
//   （阶段 2、3 在后面两章。）
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

// ---- 完成条件 ----
bool layer_done(const Stickers& s);      // DFR、DLF、DRB 都在原位原向（加上永远不动的 DBL）

// ---- 求解 ----
// 每个函数从 s 出发，返回这个阶段的转动，并把 s 推进到阶段完成之后。
Stage solve_layer(Stickers& s);

// 把已经写好的阶段串起来。s 必须是摆正过的状态。
Plan solve(const Stickers& s);

}  // namespace cube
