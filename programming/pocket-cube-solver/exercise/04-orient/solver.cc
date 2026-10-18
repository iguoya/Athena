#include "solver.hh"

#include <map>
#include <queue>
#include <stdexcept>
#include <tuple>

namespace cube {

namespace {

// 底层要装回去的三个位置。DBL 是参照，永远不动。
constexpr int kLayerSlots[3] = {4, 5, 7};  // DFR DLF DRB

std::string piece_colors(int pos) {
    std::string out;
    for (std::uint8_t c : corner_home(pos)) {
        out += color_name(c);
    }
    return out;
}

// 迭代加深：先试 1 步能不能做到，再试 2 步……第一次成功的就是这一块的最短装法。
// 同一个面不连着转两次（U 接 U 可以并成一步），分叉从 9 个砍到 6 个。
// placed：前 placed 个底层位置必须就位。前面装好的不能被弄坏，所以它们也算目标。
bool search(const Stickers& s, int depth, int last_face, int placed, Alg& path) {
    if (depth == 0) {
        for (int i = 0; i < placed; ++i) {
            if (!corner_solved(s, kLayerSlots[i])) {
                return false;
            }
        }
        return true;
    }
    for (const Move& m : basic_moves()) {
        if (static_cast<int>(m.face) == last_face) {
            continue;
        }
        path.push_back(m);
        if (search(perform(s, m), depth - 1, static_cast<int>(m.face), placed, path)) {
            return true;
        }
        path.pop_back();
    }
    return false;
}

// 一条"宏"：讲解里当作一个整体的转动。adjust 表示只是对位用的顶层转动，不是公式。
struct Macro {
    std::string title;
    std::string note;
    Alg alg;
    bool adjust;
};

// 在宏之间做最短路：每个宏的代价是它包含的转动数。顶层状态很少（几千个），
// 用 Dijkstra 直接找到总步数最少的组合，不必写一堆"遇到这种情形就怎么转"的分支。
std::vector<const Macro*> shortest(const Stickers& start, const std::vector<Macro>& macros,
                                   bool (*goal)(const Stickers&)) {
    struct Came {
        Stickers from;
        const Macro* macro = nullptr;
    };
    std::map<Stickers, Came> came;
    std::map<Stickers, int> best;
    using Item = std::tuple<int, int, Stickers>;  // 代价、入队序号、状态
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> open;
    int seq = 0;
    best[start] = 0;
    came[start] = {};
    open.push({0, seq++, start});
    while (!open.empty()) {
        const auto [cost, order, state] = open.top();
        open.pop();
        (void)order;
        if (cost > best[state]) {
            continue;
        }
        if (goal(state)) {
            std::vector<const Macro*> path;
            Stickers at = state;
            while (!(at == start)) {
                path.insert(path.begin(), came[at].macro);
                at = came[at].from;
            }
            return path;
        }
        for (const Macro& macro : macros) {
            const Stickers next = perform(state, macro.alg);
            const int next_cost = cost + static_cast<int>(macro.alg.size());
            auto it = best.find(next);
            if (it == best.end() || next_cost < it->second) {
                best[next] = next_cost;
                came[next] = {state, &macro};
                open.push({next_cost, seq++, next});
            }
        }
    }
    throw std::logic_error("宏步骤找不到解：状态不在这个阶段的范围里");
}

Stage run_macros(Stickers& s, Stage stage, const std::vector<Macro>& macros,
                 bool (*goal)(const Stickers&)) {
    for (const Macro* macro : shortest(s, macros, goal)) {
        stage.segments.push_back({macro->title, macro->note, macro->alg, {0, 1, 2, 3}});
        s = perform(s, macro->alg);
    }
    return stage;
}

std::vector<Macro> turn_macros() {
    return {
        {"转一下顶层 U", "只为对位，顶层转动不影响第一层", parse("U"), true},
        {"转一下顶层 U'", "只为对位，顶层转动不影响第一层", parse("U'"), true},
        {"转半圈顶层 U2", "只为对位，顶层转动不影响第一层", parse("U2"), true},
    };
}

}  // namespace

Alg Plan::flat() const {
    Alg out;
    for (const Stage& stage : stages) {
        for (const Segment& seg : stage.segments) {
            out.insert(out.end(), seg.moves.begin(), seg.moves.end());
        }
    }
    return out;
}

int Plan::length() const { return static_cast<int>(flat().size()); }

// ---- 完成条件 ----

bool layer_done(const Stickers& s) {
    return corner_solved(s, 4) && corner_solved(s, 5) && corner_solved(s, 6) &&
           corner_solved(s, 7);
}

bool top_oriented(const Stickers& s) {
    for (int i = 0; i < 4; ++i) {
        if (s[i] != static_cast<std::uint8_t>(Face::U)) {  // U 面的 4 格都是黄
            return false;
        }
    }
    return true;
}

std::array<int, 4> top_twists(const Stickers& s) {
    std::array<int, 4> out{};
    for (int pos = 0; pos < 4; ++pos) {
        out[pos] = -1;
        const auto& sl = corner_slots(pos);
        for (int k = 0; k < 3; ++k) {
            if (s[sl[k]] == static_cast<std::uint8_t>(Face::U)) {
                out[pos] = k;
            }
        }
    }
    return out;
}

// ---- 阶段 1：做第一层 ----

Stage solve_layer(Stickers& s) {
    Stage stage{"做第一层", "底层 4 个角块都回到原位：白色拼成一面，侧面颜色两两对上", {}};
    for (int placed = 1; placed <= 3; ++placed) {
        const int pos = kLayerSlots[placed - 1];
        if (corner_solved(s, pos)) {
            continue;
        }
        Alg path;
        bool found = false;
        for (int depth = 1; depth <= 11 && !found; ++depth) {
            path.clear();
            found = search(s, depth, -1, placed, path);
        }
        if (!found) {
            throw std::logic_error("第一层找不到解");
        }
        stage.segments.push_back({"把「" + piece_colors(pos) + "」角块装进 " + corner_name(pos),
                                  "这一块装好以后，前面装好的块仍然在原位",
                                  path,
                                  {pos}});
        s = perform(s, path);
    }
    return stage;
}

// ---- 阶段 2：翻顶面 ----

const Alg& sune() {
    static const Alg a = parse("R U R' U R U2 R'");
    return a;
}

const Alg& antisune() {
    static const Alg a = parse("R U2 R' U' R U' R'");
    return a;
}

Stage solve_orient(Stickers& s) {
    Stage stage{"翻顶面", "顶层 4 个角块的黄色全部朝上", {}};
    std::vector<Macro> macros = turn_macros();
    macros.push_back({"公式 Sune", "只改变顶层角块的朝向，第一层原样不动", sune(), false});
    macros.push_back({"公式 反 Sune", "Sune 倒着做：朝向往另一个方向拧", antisune(), false});
    return run_macros(s, stage, macros, top_oriented);
}

Plan solve(const Stickers& start) {
    if (!corner_solved(start, kDBL)) {
        throw std::invalid_argument("要先摆正：DBL 角块必须在左下后");
    }
    Plan plan;
    Stickers s = start;
    plan.stages.push_back(solve_layer(s));
    plan.stages.push_back(solve_orient(s));
    return plan;
}

}  // namespace cube
