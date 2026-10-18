#include "solver.hh"

#include <stdexcept>

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

Plan solve(const Stickers& start) {
    if (!corner_solved(start, kDBL)) {
        throw std::invalid_argument("要先摆正：DBL 角块必须在左下后");
    }
    Plan plan;
    Stickers s = start;
    plan.stages.push_back(solve_layer(s));
    return plan;
}

}  // namespace cube
