#pragma once

// 最短解：反过来搜。
//
// 层先法是"人怎么想"——先做哪一层、再做哪一层，每一步都有道理，但步数不是最少的。
// 机器可以换一种做法：从复原态出发，把每一种状态离复原最少要几步，一次性全部算出来，
// 存成一张表。之后任何状态，只要每一步都挑一个"离复原更近一步"的转法，走到头就是最短解。
//
// 状态一共 7! × 3⁶ = 3 674 160 个（DBL 固定，其余 7 块排列，朝向总和模 3 为 0，
// 所以前 6 块的朝向自由、最后一块跟着定）。一个状态一个字节，表只有 3.5 MB。

#include "cube.hh"

#include <array>
#include <vector>

namespace cube {

constexpr int kStateCount = 5040 * 729;

// 角块状态在表里的下标：排列的 Lehmer 码 × 729 + 朝向的三进制数。
int to_index(const Cubie& c);
Cubie from_index(int index);

// 在角块视角下转一步（不经过贴纸）。BFS 要转三千多万次，贴纸版太慢。
Cubie perform(const Cubie& c, Move m);

class DistanceTable {
public:
    // 从复原态做一次广度优先，填满整张表。约 3 秒。
    DistanceTable();

    int distance(const Stickers& normalized) const;
    // 最短解：每一步都走向距离减一的状态。
    Alg solve(const Stickers& normalized) const;

    // 距离为 d 的状态有多少个。histogram()[0] 是复原态自己。
    const std::vector<long>& histogram() const { return histogram_; }
    int max_distance() const { return static_cast<int>(histogram_.size()) - 1; }

private:
    std::vector<std::uint8_t> dist_;
    std::vector<long> histogram_;
};

}  // namespace cube
