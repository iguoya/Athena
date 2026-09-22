#include "pocket_cube/view.h"

#include <gtest/gtest.h>

namespace {

TEST(CubeViewTest, ThreeDViewHasFixedContentSize) {
    auto* view = make_cube_3d_view([] { return make_solved_cube(); });

    ASSERT_NE(view, nullptr);
    auto* area = dynamic_cast<Gtk::DrawingArea*>(view);
    ASSERT_NE(area, nullptr);
    EXPECT_EQ(area->get_content_width(), 240);
    EXPECT_EQ(area->get_content_height(), 240);
}

TEST(CubeViewTest, ThreeDViewHintsThatItIsDraggable) {
    auto* view = make_cube_3d_view([] { return make_solved_cube(); });

    ASSERT_NE(view, nullptr);
    EXPECT_FALSE(view->get_tooltip_text().empty());
}

TEST(CubeViewTest, NetViewHasFixedContentSize) {
    auto* view = make_cube_net_view([] { return make_solved_cube(); });

    ASSERT_NE(view, nullptr);
    auto* area = dynamic_cast<Gtk::DrawingArea*>(view);
    ASSERT_NE(area, nullptr);
    EXPECT_EQ(area->get_content_width(), 240);
    EXPECT_EQ(area->get_content_height(), 180);
}

// 下一步穷举九宫格需要把两种视图都缩小塞进小格子里（见 main.cc 的
// make_cube_state_block()），尺寸参数必须真的生效。
TEST(CubeViewTest, ThreeDViewAcceptsCustomSize) {
    auto* view = make_cube_3d_view([] { return make_solved_cube(); }, 90);

    auto* area = dynamic_cast<Gtk::DrawingArea*>(view);
    ASSERT_NE(area, nullptr);
    EXPECT_EQ(area->get_content_width(), 90);
    EXPECT_EQ(area->get_content_height(), 90);
}

TEST(CubeViewTest, NetViewAcceptsCustomSize) {
    auto* view = make_cube_net_view([] { return make_solved_cube(); }, 96, 72);

    auto* area = dynamic_cast<Gtk::DrawingArea*>(view);
    ASSERT_NE(area, nullptr);
    EXPECT_EQ(area->get_content_width(), 96);
    EXPECT_EQ(area->get_content_height(), 72);
}

TEST(CubeViewTest, StateSpaceRingsViewHasFixedContentSize) {
    auto* view = make_state_space_rings_view();

    ASSERT_NE(view, nullptr);
    auto* area = dynamic_cast<Gtk::DrawingArea*>(view);
    ASSERT_NE(area, nullptr);
    EXPECT_EQ(area->get_content_width(), 320);
    EXPECT_EQ(area->get_content_height(), 320);
}

TEST(CubeViewTest, StateSpaceRingsViewAcceptsCustomSize) {
    auto* view = make_state_space_rings_view(3'674'160, 150);

    auto* area = dynamic_cast<Gtk::DrawingArea*>(view);
    ASSERT_NE(area, nullptr);
    EXPECT_EQ(area->get_content_width(), 150);
    EXPECT_EQ(area->get_content_height(), 150);
}

// 状态空间数量是唯一驱动环上点数的输入，哪怕是 1（最小的合法值）也
// 不该崩溃或产生负数点数——draw_state_space_rings() 里 max(6, ...)
// 兜底保证至少有 6 个点，这里只验证构造和挂载本身不出错。
TEST(CubeViewTest, StateSpaceRingsViewAcceptsSmallStateSpace) {
    auto* view = make_state_space_rings_view(1, 100);

    ASSERT_NE(view, nullptr);
    EXPECT_FALSE(view->get_tooltip_text().empty());
}

} // namespace

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    const auto application =
        Gtk::Application::create("cn.athena.practice.pocketcube.tests");
    return RUN_ALL_TESTS();
}
