#include "render/cube_view.h"

#include <gtest/gtest.h>

namespace {

TEST(CubeViewTest, CreatesADrawingAreaWithFixedContentSize) {
    auto* view = make_cube_3d_view();

    ASSERT_NE(view, nullptr);
    auto* area = dynamic_cast<Gtk::DrawingArea*>(view);
    ASSERT_NE(area, nullptr);
    EXPECT_EQ(area->get_content_width(), 280);
    EXPECT_EQ(area->get_content_height(), 280);
}

TEST(CubeViewTest, HintsThatItIsDraggable) {
    auto* view = make_cube_3d_view();

    ASSERT_NE(view, nullptr);
    EXPECT_FALSE(view->get_tooltip_text().empty());
}

} // namespace
