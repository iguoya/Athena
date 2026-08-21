#include "ui/progress_page.h"
#include "render/chart_view.h"

#include <gtest/gtest.h>

namespace {

Gtk::Label* find_label(Gtk::Widget& root, const string& text) {
    if (auto* label = dynamic_cast<Gtk::Label*>(&root);
        label && label->get_text() == text) {
        return label;
    }
    for (auto* child = root.get_first_child(); child;
         child = child->get_next_sibling()) {
        if (auto* label = find_label(*child, text)) {
            return label;
        }
    }
    return nullptr;
}

Gtk::Expander* find_expander(Gtk::Widget& root) {
    if (auto* expander = dynamic_cast<Gtk::Expander*>(&root)) {
        return expander;
    }
    for (auto* child = root.get_first_child(); child;
         child = child->get_next_sibling()) {
        if (auto* expander = find_expander(*child)) {
            return expander;
        }
    }
    return nullptr;
}

TEST(ProgressPageTest, RendersAggregatedDataWithoutReadingStorage) {
    const CategoryProgress progress {
        .chapters = {
            {
                .chapter_title = "RAII",
                .subchapter_mastery = {{"资源所有权", 5}, {"析构清理", 3}},
                .total = 2,
                .mastered = 1,
                .in_progress = 1,
                .mastery_sum = 8,
            },
        },
        .total = 2,
        .mastered = 1,
        .in_progress = 1,
        .not_started = 0,
        .mastery_sum = 8,
    };

    auto* page = make_progress_page("测试分类", progress);

    ASSERT_NE(page, nullptr);
    EXPECT_TRUE(page->has_css_class("progress-page"));
    EXPECT_NE(find_label(*page, "学习进度 · 测试分类"), nullptr);
    EXPECT_NE(find_label(*page, "知识点总数"), nullptr);
    EXPECT_NE(find_label(*page, "4.0 / 5"), nullptr);
    EXPECT_NE(find_label(*page, "RAII"), nullptr);
    EXPECT_NE(find_label(*page, "1/2"), nullptr);
    auto* chapter = find_expander(*page);
    ASSERT_NE(chapter, nullptr);
    ASSERT_NE(chapter->get_child(), nullptr);
    EXPECT_NE(find_label(*chapter->get_child(), "资源所有权"), nullptr);
}

TEST(ProgressPageTest, DonutReservesSpaceForItsFullStroke) {
    auto* donut = make_mastery_donut_chart(1, 2, 3);

    EXPECT_EQ(donut->get_content_width(), 230);
    EXPECT_EQ(donut->get_content_height(), 230);
}

} // namespace
