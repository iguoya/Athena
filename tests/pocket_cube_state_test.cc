#include "practice/pocket_cube/state.h"

#include <gtest/gtest.h>

#include <cmath>

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

// 顺时针的方向必须符合“站在这个面外侧、面对这个面看，标准时钟顺时针”
// 这个真实定义，不能只是内部自洽（上面几条群论性质——转 4 次回原点、
// 顺逆抵消、180=2x90——即使顺逆时针整体反了也照样成立，抓不出方向
// 错误）。这里挑 URF 这一个角块，跟踪它身上某个贴纸转完一步之后跑到
// 了哪个面，用具体坐标断言，而不是靠“看起来应该对”这种主观判断：
//   U 顺时针（从上往下看，标准循环 F→R→B→L→F）：
//     URF 贴的 F 面颜色转完之后应该出现在 R 面的 UBR 格。
//   R 顺时针（从右边看，标准循环 U→F→D→B→U）：
//     URF 贴的 F 面颜色转完之后应该出现在 D 面的 DRF 格。
//   F 顺时针（从前面看，标准循环 U→L→D→R→U）：
//     URF 贴的 U 面颜色转完之后应该出现在 L 面的 ULF 格。
// 这三条断言只有转动方向真的对了才会通过，方向反了会在这里直接失败。
// 注意：这条测试断言的是 apply_move() 的计算语义，跟界面上 R/F 两个
// 面转法标签显示成什么文字（move_label()/move_description()）是两回
// 事——那两个函数为了跟实际观感对齐做了针对性调整，不代表这里的计算
// 方向也跟着变，见 move_label() 的注释。
TEST(CubeStateTest, ClockwiseMatchesStandardVisualDefinition) {
    const CubeState solved = make_solved_cube();

    const CubeState turned_u = apply_move(solved, {Face::U, Turn::Clockwise});
    EXPECT_EQ(sticker_at(turned_u, Face::R, /*u=y*/ 1, /*v=z*/ -1), Face::F)
        << "U 顺时针后，F 面颜色应该出现在 R 面（F→R）";

    const CubeState turned_r = apply_move(solved, {Face::R, Turn::Clockwise});
    EXPECT_EQ(sticker_at(turned_r, Face::D, /*u=x*/ 1, /*v=z*/ 1), Face::F)
        << "R 顺时针后，F 面颜色应该出现在 D 面（F→D）";

    const CubeState turned_f = apply_move(solved, {Face::F, Turn::Clockwise});
    EXPECT_EQ(sticker_at(turned_f, Face::L, /*u=y*/ 1, /*v=z*/ 1), Face::U)
        << "F 顺时针后，U 面颜色应该出现在 L 面（U→L）";
}

// turn_angle_degrees() 给 3D 转动动画用，角度必须和 apply_move() 真实
// 的坐标跳变严格对应：把这一层里的角块坐标绕 face_layout(move.face).
// normal_axis 转这个角度（标准数学定义，右手定则），应该正好落在
// apply_move() 算出的新坐标上。两者一旦对不上，动画播完的瞬间画面会
// 跟实际状态错位或者跳一下，这条测试直接把两边摆在一起比较，不靠
// 肉眼盯着动画帧判断。
TEST(CubeStateTest, TurnAngleDegreesMatchesActualCoordinateChange) {
    const CubeState solved = make_solved_cube();
    for (const Move& move : next_move_set()) {
        const CubeState turned = apply_move(solved, move);
        const double radians = turn_angle_degrees(move) * M_PI / 180.0;
        const FaceLayout layout = face_layout(move.face);

        for (size_t i = 0; i < solved.corners.size(); ++i) {
            const auto& before = solved.corners[i];
            const int before_axis_value = layout.normal_axis == Axis::X
                ? before.x
                : (layout.normal_axis == Axis::Y ? before.y : before.z);
            if (before_axis_value != layout.normal_sign) {
                continue; // 不在这一层的角块，转动跟它无关。
            }

            double new_x = before.x, new_y = before.y, new_z = before.z;
            switch (layout.normal_axis) {
            case Axis::X:
                new_y = before.y * cos(radians) - before.z * sin(radians);
                new_z = before.y * sin(radians) + before.z * cos(radians);
                break;
            case Axis::Y:
                new_x = before.x * cos(radians) + before.z * sin(radians);
                new_z = -before.x * sin(radians) + before.z * cos(radians);
                break;
            case Axis::Z:
                new_x = before.x * cos(radians) - before.y * sin(radians);
                new_y = before.x * sin(radians) + before.y * cos(radians);
                break;
            }

            const auto& after = turned.corners[i];
            EXPECT_NEAR(new_x, after.x, 1e-9) << "move=" << move_label(move);
            EXPECT_NEAR(new_y, after.y, 1e-9) << "move=" << move_label(move);
            EXPECT_NEAR(new_z, after.z, 1e-9) << "move=" << move_label(move);
        }
    }
}

// 下一步穷举集合只应该覆盖 U/R/F 三个面（D/L/B 是冗余转法），每个面
// 恰好 3 种幅度，互不重复——这是“九宫格里不会有两格显示同一个转法”
// 这个前提能推出的必然性质。
TEST(CubeStateTest, NextMoveSetCoversUrfWithNoDuplicates) {
    const array<Move, 9> moves = next_move_set();
    EXPECT_EQ(moves.size(), 9u);
    for (const Move& move : moves) {
        EXPECT_TRUE(
            move.face == Face::U || move.face == Face::R || move.face == Face::F);
    }
    for (size_t i = 0; i < moves.size(); ++i) {
        for (size_t j = i + 1; j < moves.size(); ++j) {
            EXPECT_FALSE(
                moves[i].face == moves[j].face && moves[i].turn == moves[j].turn)
                << "duplicate move at indices " << i << " and " << j;
        }
    }
}

TEST(CubeStateTest, MoveLabelUsesStandardNotation) {
    EXPECT_EQ(move_label({Face::U, Turn::Clockwise}), "U");
    EXPECT_EQ(move_label({Face::U, Turn::CounterClockwise}), "U'");
    EXPECT_EQ(move_label({Face::U, Turn::Half}), "U2");
    EXPECT_EQ(move_label({Face::F, Turn::Half}), "F2");
}

// R、F 这两个面的顺时针/逆时针文字标签是互换过的（跟 apply_move() 的
// 计算语义无关，只影响展示文字，见 state.cc 里 display_turn() 的注释）
// ——U/D/L/B 不受影响，Half 因为顺逆效果一样也不受影响。
TEST(CubeStateTest, RAndFLabelsAreSwappedButHalfAndOtherFacesAreNot) {
    EXPECT_EQ(move_label({Face::R, Turn::Clockwise}), "R'");
    EXPECT_EQ(move_label({Face::R, Turn::CounterClockwise}), "R");
    EXPECT_EQ(move_label({Face::R, Turn::Half}), "R2");
    EXPECT_EQ(move_label({Face::F, Turn::Clockwise}), "F'");
    EXPECT_EQ(move_label({Face::F, Turn::CounterClockwise}), "F");
    EXPECT_EQ(move_label({Face::D, Turn::Clockwise}), "D");
    EXPECT_EQ(move_label({Face::L, Turn::CounterClockwise}), "L'");
    EXPECT_EQ(move_label({Face::B, Turn::Clockwise}), "B");
}

TEST(CubeStateTest, MoveDescriptionIsNonEmptyForEveryNextMove) {
    for (const Move& move : next_move_set()) {
        EXPECT_FALSE(move_description(move).empty());
    }
}

} // namespace
