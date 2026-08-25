#include "practice/pocket_cube/view.h"

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

// 下一步穷举九宫格需要把两种视图都缩小塞进小格子里（见
// MainWindow::initialize_practice_page()），尺寸参数必须真的生效。
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

} // namespace
