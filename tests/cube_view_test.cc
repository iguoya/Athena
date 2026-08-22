#include "render/cube_view.h"

#include <gtest/gtest.h>

namespace {

TEST(CubeViewTest, CreatesADrawingAreaWithFixedContentSize) {
    auto* view = make_cube_isometric_view();

    ASSERT_NE(view, nullptr);
    EXPECT_EQ(view->get_content_width(), 240);
    EXPECT_EQ(view->get_content_height(), 240);
}

} // namespace
