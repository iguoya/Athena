// 模型与求解的测试。不依赖 GTK。

#include "cube.hh"
#include "solver.hh"

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

// 随机合法状态：8 个角块任意排列、朝向任意（总和模 3 为 0）。DBL 可能不在原位。
Stickers random_state(std::mt19937& rng) {
    Cubie c{};
    std::array<int, kCorners> order{};
    for (int i = 0; i < kCorners; ++i) {
        order[i] = i;
    }
    std::shuffle(order.begin(), order.end(), rng);
    int sum = 0;
    for (int i = 0; i < kCorners; ++i) {
        c.piece[i] = static_cast<std::uint8_t>(order[i]);
        c.twist[i] = static_cast<std::uint8_t>(i < kCorners - 1 ? rng() % 3 : (3 - sum % 3) % 3);
        sum += c.twist[i];
    }
    return stickers_of(c);
}

}  // namespace

int main() {
    std::mt19937 rng(20261018);

    // 贴纸位的约定：展开图上 U 面第 0 格在左后角，F 面第 0 格在左上前角。
    EXPECT(slot(0).pos == (Vec{-1, 1, -1}));
    EXPECT(slot(8).pos == (Vec{-1, 1, 1}));
    EXPECT(is_solved(solved()));

    // 记号往返。
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
        EXPECT(u[8] == static_cast<int>(Face::R) && u[9] == static_cast<int>(Face::R));  // F 面上排换成原来的 R
        const Stickers f = after("F");
        EXPECT(f[4] == static_cast<int>(Face::U));  // R 面（F 一侧）收到 U 的颜色
    }

    // 转动的数学性质。
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
            EXPECT((i == 5) == is_solved(s));
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

    // 角块视角：往返、朝向和为 3 的倍数、DBL 不动。
    for (int round = 0; round < 200; ++round) {
        const Stickers s = random_state(rng);
        EXPECT(diagnose(s).empty());
        EXPECT(stickers_of(cubie_of(s)) == s);
        int sum = 0;
        for (auto t : cubie_of(s).twist) {
            sum += t;
        }
        EXPECT(sum % 3 == 0);
    }
    {
        Stickers s = solved();
        for (int i = 0; i < 300; ++i) {
            s = perform(s, basic_moves()[rng() % 9]);
            EXPECT(corner_solved(s, kDBL));
            EXPECT(diagnose(s).empty());
        }
    }

    // 不合法的输入要说得出原因。
    {
        Stickers s = solved();
        std::swap(s[0], s[4]);  // U 的一格和 R 的一格互换
        EXPECT(!diagnose(s).empty());
        Stickers twisted = solved();  // 单独拧一个角块
        const auto& sl = corner_slots(0);
        const auto a = twisted[sl[0]], b = twisted[sl[1]], c = twisted[sl[2]];
        twisted[sl[0]] = c;
        twisted[sl[1]] = a;
        twisted[sl[2]] = b;
        EXPECT(diagnose(twisted).find("拧过") != std::string::npos);
        Stickers mirrored = solved();
        std::swap(mirrored[corner_slots(0)[1]], mirrored[corner_slots(0)[2]]);
        EXPECT(diagnose(mirrored).find("反了") != std::string::npos);
        Stickers counts = solved();
        counts[0] = static_cast<std::uint8_t>(Face::R);
        EXPECT(diagnose(counts).find("格") != std::string::npos);
    }

    // 讲解里的公式：只动该动的，其余原样。
    {
        const Stickers sn = perform(solved(), sune());
        EXPECT(layer_done(sn));  // 第一层不受影响
        EXPECT(top_twists(sn) != (std::array<int, 4>{0, 0, 0, 0}));
        EXPECT(is_solved(perform(sn, antisune())));
        const Stickers adj = perform(solved(), swap_adjacent());
        const Stickers dia = perform(solved(), swap_diagonal());
        for (const Stickers* s : {&adj, &dia}) {
            EXPECT(layer_done(*s));
            EXPECT(top_oriented(*s));  // 只换位置，不改朝向
            const Cubie c = cubie_of(*s);
            int moved = 0;
            for (int pos = 0; pos < 4; ++pos) {
                moved += c.piece[pos] != pos;
                EXPECT(c.twist[pos] == 0);
            }
            EXPECT(moved == 2);
        }
        // 相邻交换：被换的两块在顶层环上相邻；对角交换：相隔一块。
        const auto where = [](const Cubie& c) {
            std::vector<int> v;
            for (int pos = 0; pos < 4; ++pos) {
                if (c.piece[pos] != pos) {
                    v.push_back(pos);
                }
            }
            return (v[1] - v[0]) % 2 == 1;  // 环上相邻
        };
        EXPECT(where(cubie_of(adj)));
        EXPECT(!where(cubie_of(dia)));
    }

    // 摆正：任意姿势的合法魔方都能摆正，换算回去的转法同样有效。
    for (int round = 0; round < 300; ++round) {
        const Stickers s = random_state(rng);
        const Oriented o = normalize(s);
        EXPECT(corner_solved(o.state, kDBL));
        const Plan plan = solve(o.state);
        EXPECT(is_solved(perform(o.state, plan.flat())));
        const Stickers back = perform(s, to_input_frame(plan.flat(), o));
        EXPECT(normalize(back).state == solved());
    }

    // 三阶段流水线：随机状态必须复原，并且逐阶段满足各自的完成条件。
    int longest = 0;
    long total = 0;
    const int rounds = 2000;
    for (int round = 0; round < rounds; ++round) {
        const Stickers s = random_normalized(rng);
        const Plan plan = solve(s);
        Stickers at = s;
        const bool (*done[3])(const Stickers&) = {nullptr, nullptr, nullptr};
        (void)done;
        for (std::size_t i = 0; i < plan.stages.size(); ++i) {
            for (const Segment& seg : plan.stages[i].segments) {
                at = perform(at, seg.moves);
            }
            if (i == 0) {
                EXPECT(layer_done(at));
            } else if (i == 1) {
                EXPECT(layer_done(at) && top_oriented(at));
            } else {
                EXPECT(is_solved(at));
            }
        }
        longest = std::max(longest, plan.length());
        total += plan.length();
    }
    std::cout << "层先法：" << rounds << " 个随机状态全部复原，最长 " << longest << " 步，平均 "
              << static_cast<double>(total) / rounds << " 步\n";

    // 已经复原的魔方不需要任何转动。
    EXPECT(solve(solved()).length() == 0);

    if (failures != 0) {
        std::cerr << failures << " 项失败\n";
        return 1;
    }
    std::cout << "全部通过\n";
    return 0;
}
