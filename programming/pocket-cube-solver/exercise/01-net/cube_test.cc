// 手抄的角块表不能抄错：每张贴纸恰好属于一个角块，每个角块的三种颜色互不相同，
// 并且 8 个角块的颜色组合各不相同——真魔方就是这样。

#include "cube.hh"

#include <algorithm>
#include <array>
#include <iostream>
#include <set>

using namespace cube;

namespace {

int failures = 0;

void expect(bool condition, int line) {
    if (!condition) {
        std::cerr << "FAIL line " << line << "\n";
        ++failures;
    }
}
#define EXPECT(cond) expect((cond), __LINE__)

}  // namespace

int main() {
    // 24 张贴纸，每张恰好出现在一个角块里。
    std::array<int, kStickers> seen{};
    for (const auto& corner : corner_slots()) {
        for (int s : corner) {
            ++seen[s];
        }
    }
    EXPECT(std::all_of(seen.begin(), seen.end(), [](int n) { return n == 1; }));

    // 复原态下，每个角块的三张贴纸颜色互不相同，且 8 种组合各不相同；
    // 每个角块有且只有一张黄或白（上下两个面的颜色）。
    std::set<std::set<int>> combos;
    const Stickers s = solved();
    for (int c = 0; c < kCorners; ++c) {
        std::set<int> colors;
        int top_bottom = 0;
        for (int slot : corner_slots()[c]) {
            colors.insert(s[slot]);
            top_bottom += s[slot] == 0 || s[slot] == 3;
        }
        EXPECT(colors.size() == 3);
        EXPECT(top_bottom == 1);
        combos.insert(colors);
        EXPECT(corner_of(corner_slots()[c][1]) == c);
    }
    EXPECT(combos.size() == 8);

    // 配色手性：DBL 角块的三张贴纸，从下面那张起顺时针是白、蓝、红，
    // 也就是红、白、蓝顺时针（维基百科 Rubik's Cube 的标准配色）。
    {
        const auto& dbl = corner_slots()[6];
        EXPECT(s[dbl[0]] == 3 && s[dbl[1]] == 5 && s[dbl[2]] == 4);
    }

    // 例子里每种颜色恰好 4 张。
    std::array<int, 6> count{};
    for (int i = 0; i < kStickers; ++i) {
        ++count[sample()[i]];
    }
    EXPECT(std::all_of(count.begin(), count.end(), [](int n) { return n == 4; }));

    if (failures != 0) {
        std::cerr << failures << " 项失败\n";
        return 1;
    }
    std::cout << "全部通过\n";
    return 0;
}
