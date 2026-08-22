#include "render/cube_view.h"

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

} // namespace
