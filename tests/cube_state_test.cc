#include "render/cube_state.h"

#include <gtest/gtest.h>

namespace {

bool states_equal(const CubeState& a, const CubeState& b) {
    for (size_t i = 0; i < a.corners.size(); ++i) {
        const auto& ca = a.corners[i];
        const auto& cb = b.corners[i];
        if (ca.x != cb.x || ca.y != cb.y || ca.z != cb.z ||
            ca.color_x != cb.color_x || ca.color_y != cb.color_y ||
            ca.color_z != cb.color_z) {
            return false;
        }
    }
    return true;
}

const array<Face, 6> kAllFaces = {
    Face::U, Face::D, Face::L, Face::R, Face::F, Face::B};

TEST(CubeStateTest, SolvedCubeIsSolved) {
    EXPECT_TRUE(is_solved(make_solved_cube()));
}

TEST(CubeStateTest, EveryFaceStartsUniform) {
    const CubeState solved = make_solved_cube();
    for (const Face face : kAllFaces) {
        const Face expected = sticker_at(solved, face, -1, -1);
        for (int u : {-1, 1}) {
            for (int v : {-1, 1}) {
                EXPECT_EQ(sticker_at(solved, face, u, v), expected)
                    << "face mismatch within a solved face";
            }
        }
    }
}

// 代数自检：任意一个面转 4 次 90 度，必须回到原状态——这是"合法的
// 90 度旋转"这个前提能推出的必然性质，不依赖我对"哪个颜色该转到哪"
// 的主观判断，能有效抓出旋转矩阵实现里的符号错误。
TEST(CubeStateTest, FourQuarterTurnsReturnToStart) {
    const CubeState solved = make_solved_cube();
    for (const Face face : kAllFaces) {
        CubeState state = solved;
        for (int i = 0; i < 4; ++i) {
            state = apply_move(state, {face, Turn::Clockwise});
        }
        EXPECT_TRUE(states_equal(state, solved))
            << "four clockwise turns did not return to start";
    }
}

TEST(CubeStateTest, ClockwiseThenCounterClockwiseCancelsOut) {
    const CubeState solved = make_solved_cube();
    for (const Face face : kAllFaces) {
        CubeState state = apply_move(solved, {face, Turn::Clockwise});
        state = apply_move(state, {face, Turn::CounterClockwise});
        EXPECT_TRUE(states_equal(state, solved));
    }
}

TEST(CubeStateTest, HalfTurnEqualsTwoClockwiseTurns) {
    const CubeState solved = make_solved_cube();
    for (const Face face : kAllFaces) {
        CubeState twice = apply_move(solved, {face, Turn::Clockwise});
        twice = apply_move(twice, {face, Turn::Clockwise});
        const CubeState half = apply_move(solved, {face, Turn::Half});
        EXPECT_TRUE(states_equal(twice, half));
    }
}

// 转动只应该影响这一层的 4 个角块，另外 4 个原地不动。
TEST(CubeStateTest, TurnOnlyMovesTheSelectedLayer) {
    const CubeState solved = make_solved_cube();
    const CubeState turned = apply_move(solved, {Face::U, Turn::Clockwise});
    int unchanged = 0;
    for (size_t i = 0; i < solved.corners.size(); ++i) {
        if (solved.corners[i].y < 0) {
            const auto& before = solved.corners[i];
            const auto& after = turned.corners[i];
            EXPECT_EQ(before.x, after.x);
            EXPECT_EQ(before.y, after.y);
            EXPECT_EQ(before.z, after.z);
            ++unchanged;
        }
    }
    EXPECT_EQ(unchanged, 4);
    EXPECT_FALSE(is_solved(turned));
}

// 每个面转一次以后，这个面本身的 4 个贴纸颜色应该保持不变（这一层的
// 4 个角块只是彼此换位置，各自朝这个面方向的贴纸颜色不受影响）。
TEST(CubeStateTest, TurningAFaceKeepsItsOwnStickersUnchanged) {
    const CubeState solved = make_solved_cube();
    for (const Face face : kAllFaces) {
        const CubeState turned = apply_move(solved, {face, Turn::Clockwise});
        for (int u : {-1, 1}) {
            for (int v : {-1, 1}) {
                EXPECT_EQ(
                    sticker_at(solved, face, u, v), sticker_at(turned, face, u, v));
            }
        }
    }
}

} // namespace
