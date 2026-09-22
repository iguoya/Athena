#include "practice/pocket_cube/pocket_cube.hpp"

#include <gtest/gtest.h>

#include <sstream>

namespace {

TEST(PocketCubeTest, StartsSolvedWithEmptyHistory) {
    PocketCube cube;
    EXPECT_TRUE(is_solved(cube.state()));
    EXPECT_TRUE(cube.move_history().empty());
}

// run() 目前固定转一次 U 顺时针，这是 PocketCube 当前唯一的知识点
// 入口——history 应该忠实记下这一步，不是只记步数。
TEST(PocketCubeTest, RunAppendsExactlyTheAppliedMoveToHistory) {
    PocketCube cube;
    ostringstream output;
    cube.run(output);

    ASSERT_EQ(cube.move_history().size(), 1u);
    EXPECT_EQ(cube.move_history().front().face, Face::U);
    EXPECT_EQ(cube.move_history().front().turn, Turn::Clockwise);
    EXPECT_FALSE(is_solved(cube.state()));
}

TEST(PocketCubeTest, HistoryAccumulatesAcrossMultipleRuns) {
    PocketCube cube;
    for (int i = 0; i < 4; ++i) {
        ostringstream output;
        cube.run(output);
    }
    EXPECT_EQ(cube.move_history().size(), 4u);
    // U 转 4 次 90 度顺时针等于转回原状态，跟 state_test 里的代数自检
    // 是同一个性质，这里换个角度确认 run() 真的在调 apply_move。
    EXPECT_TRUE(is_solved(cube.state()));
}

// next_states() 不应该改动 m_state，且要跟 next_move_set() 给出的 9
// 种转法一一对应、结果等于对当前状态单独 apply_move() 一次。
TEST(PocketCubeTest, NextStatesMatchesNextMoveSetWithoutMutatingState) {
    PocketCube cube;
    ostringstream output;
    cube.run(output);
    const CubeState before = cube.state();

    const auto moves = next_move_set();
    const auto next_states = cube.next_states();
    ASSERT_EQ(next_states.size(), moves.size());
    for (size_t i = 0; i < moves.size(); ++i) {
        EXPECT_EQ(next_states[i].first.face, moves[i].face);
        EXPECT_EQ(next_states[i].first.turn, moves[i].turn);

        const CubeState expected = apply_move(before, moves[i]);
        for (size_t c = 0; c < expected.corners.size(); ++c) {
            EXPECT_EQ(next_states[i].second.corners[c].x, expected.corners[c].x);
            EXPECT_EQ(next_states[i].second.corners[c].y, expected.corners[c].y);
            EXPECT_EQ(next_states[i].second.corners[c].z, expected.corners[c].z);
        }
    }

    // 状态本身没有被 next_states() 悄悄改掉。
    for (size_t c = 0; c < before.corners.size(); ++c) {
        EXPECT_EQ(cube.state().corners[c].x, before.corners[c].x);
        EXPECT_EQ(cube.state().corners[c].y, before.corners[c].y);
        EXPECT_EQ(cube.state().corners[c].z, before.corners[c].z);
    }
}

} // namespace
