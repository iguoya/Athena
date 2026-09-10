#include "render/knowledge_graph_view.h"

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

Gtk::Button* find_graph_node(Gtk::Widget& root) {
    if (auto* button = dynamic_cast<Gtk::Button*>(&root);
        button && button->has_css_class("knowledge-graph-node")) {
        return button;
    }
    for (auto* child = root.get_first_child(); child;
         child = child->get_next_sibling()) {
        if (auto* button = find_graph_node(*child)) {
            return button;
        }
    }
    return nullptr;
}

TEST(KnowledgeGraphViewTest, RendersRichChapterNodeAndMetricLegend) {
    const KnowledgeGraph graph{
        .nodes = {{
            .chapter_name = "Chapter",
            .title = "测试章节",
            .description = "用于验证节点卡片信息密度",
            .icon = {.type = "theme", .name = "applications-development-symbolic"},
            .layer = 0,
            .slot = 0,
            .layer_size = 1,
            .total = 2,
            .mastered = 1,
            .difficulty = 4,
            .completion = 0.7,
        }},
        .layer_count = 1,
    };

    string opened_chapter;
    auto* view = make_knowledge_graph_view(
        graph,
        [&opened_chapter](const string& chapter_name) {
            opened_chapter = chapter_name;
        });

    ASSERT_NE(view, nullptr);
    auto* node = find_graph_node(*view);
    ASSERT_NE(node, nullptr);
    const auto size_request = node->get_size_request();
    EXPECT_EQ(size_request.get_width(), -1);
    EXPECT_EQ(size_request.get_height(), -1);
    EXPECT_TRUE(view->get_hexpand());
    EXPECT_NE(find_label(*view, "测试章节"), nullptr);
    auto* description = find_label(*view, "用于验证节点卡片信息密度");
    ASSERT_NE(description, nullptr);
    EXPECT_TRUE(description->get_wrap());
    EXPECT_EQ(description->get_ellipsize(), Pango::EllipsizeMode::NONE);
    EXPECT_EQ(description->get_lines(), -1);
    EXPECT_NE(find_label(*view, "难度 4/5"), nullptr);
    EXPECT_NE(find_label(*view, "掌握 1/2"), nullptr);
    EXPECT_NE(find_label(*view, "完成 70%"), nullptr);
    EXPECT_NE(find_label(*view, "图谱说明"), nullptr);
    EXPECT_NE(find_label(*view, "章节难度"), nullptr);
    EXPECT_NE(find_label(*view, "掌握程度"), nullptr);
    EXPECT_NE(find_label(*view, "完成程度"), nullptr);

    g_signal_emit_by_name(node->gobj(), "clicked");
    EXPECT_EQ(opened_chapter, "Chapter");
}

} // namespace
