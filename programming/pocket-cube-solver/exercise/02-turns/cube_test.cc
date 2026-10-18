// 模型与转动的测试。不依赖 GTK。

#include "cube.hh"

#include <algorithm>
#include <iostream>
#include <random>

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

Stickers after(const char* alg) { return perform(solved(), parse(alg)); }

// 左下后角块 DBL 的三张贴纸还是原来的颜色。
bool dbl_untouched(const Stickers& s) {
    return s[slot_index({-1, -1, -1}, {0, -1, 0})] == static_cast<int>(Face::D) &&
           s[slot_index({-1, -1, -1}, {0, 0, -1})] == static_cast<int>(Face::B) &&
           s[slot_index({-1, -1, -1}, {-1, 0, 0})] == static_cast<int>(Face::L);
}

}  // namespace

int main() {
    std::mt19937 rng(20261018);

    // 贴纸位的约定：展开图上 U 面第 0 格在左后角，F 面第 0 格在左上前角。
    EXPECT(slot(0).pos == (Vec{-1, 1, -1}));
    EXPECT(slot(8).pos == (Vec{-1, 1, 1}));
    EXPECT(is_solved(solved()));

    // 记号往返，写错的记号要报错。
    EXPECT(to_string(parse("R U R' U2 F")) == "R U R' U2 F");
    bool threw = false;
    try {
        parse("X");
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    EXPECT(threw);

    // 转动方向：R 把前面一列翻到顶上，U 把前面转到左边，F 把顶上转到右边。
    {
        const Stickers r = after("R");
        EXPECT(r[1] == static_cast<int>(Face::F) && r[3] == static_cast<int>(Face::F));  // U 面右列
        const Stickers u = after("U");
        EXPECT(u[8] == static_cast<int>(Face::R) && u[9] == static_cast<int>(Face::R));  // F 面上排
        const Stickers f = after("F");
        EXPECT(f[4] == static_cast<int>(Face::U));  // R 面靠 F 的一列收到 U 的颜色
    }

    // 转动的数学性质：转四次回到原样；逆转抵消；转两次等于转半圈。
    for (const char* name : {"U", "R", "F", "D", "L", "B"}) {
        Stickers s = solved();
        for (int i = 0; i < 4; ++i) {
            s = perform(s, parse(name));
        }
        EXPECT(is_solved(s));
        EXPECT(is_solved(perform(after(name), parse(std::string(name) + "'"))));
        EXPECT(after((std::string(name) + "2").c_str()) == after((std::string(name) + " " + name).c_str()));
    }
    {
        Stickers s = solved();
        for (int i = 0; i < 6; ++i) {
            s = perform(s, parse("R U R' U'"));
            EXPECT((i == 5) == is_solved(s));  // 这个四步组合要重复 6 次才回到原样
        }
    }

    // 配色手性：红、白、蓝绕 DBL 角块顺时针（维基百科 Rubik's Cube 的标准配色）。
    // 从角块外面看，na→nb→nc 顺时针，当且仅当 (na × nb)·外向 < 0。
    {
        const Vec out{-1, -1, -1};
        const Vec red = face_normal(Face::L), white = face_normal(Face::D), blue = face_normal(Face::B);
        const auto clockwise = [&](Vec a, Vec b) {
            const Vec c{a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
            return c.x * out.x + c.y * out.y + c.z * out.z < 0;
        };
        EXPECT(clockwise(red, white) && clockwise(white, blue) && clockwise(blue, red));
    }

    // 黄金向量：和 scripts/cube_golden.json 里的条目逐字相同。网页讲解里的小模型也拿它们核对，
    // 两份实现（C++ 与 TypeScript）因此不会悄悄分叉。
    {
        const struct {
            const char* alg;
            const char* state;
        } golden[] = {
        {"U", "000055111122333322444455"},
        {"R", "020211112323353544440505"},
        {"F", "004401012222113343435555"},
        {"D", "000011222244333344555511"},
        {"L'", "202011113232535344445050"},
        {"B2", "330014142222330014145555"},
        {"R U R' U'", "040210012322313354445155"},
        {"R U R' U R U2 R'", "201504110422333305442155"},
        {"F R U' R' U' R U R' F'", "201042110522333345441055"},
        {"R U F' U2 R2 F U'", "451214525310213023400345"},
        {"D L B' R2 U F2", "555243513020312001344421"},
        };
        for (const auto& g : golden) {
            std::string text;
            for (std::uint8_t c : after(g.alg)) {
                text += static_cast<char>('0' + c);
            }
            EXPECT(text == g.state);
        }
    }

    // 只转 U、R、F 的时候，DBL 角块永远不动，这是整个解法的参照。
    {
        Stickers s = solved();
        for (int i = 0; i < 300; ++i) {
            s = perform(s, basic_moves()[rng() % 9]);
            EXPECT(dbl_untouched(s));
        }
        const Alg scramble = random_alg(rng, 25);
        EXPECT(scramble.size() == 25);
        EXPECT(dbl_untouched(perform(solved(), scramble)));
        EXPECT(is_solved(perform(perform(solved(), scramble), inverse(scramble))));
    }

    if (failures != 0) {
        std::cerr << failures << " 项失败\n";
        return 1;
    }
    std::cout << "全部通过\n";
    return 0;
}
