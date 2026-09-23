#include "ui/progress_overview.h"
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

Gtk::Frame* find_frame(Gtk::Widget& root, const string& label) {
    if (auto* frame = dynamic_cast<Gtk::Frame*>(&root);
        frame && frame->get_label() == label) {
        return frame;
    }
    for (auto* child = root.get_first_child(); child;
         child = child->get_next_sibling()) {
        if (auto* frame = find_frame(*child, label)) {
            return frame;
        }
    }
    return nullptr;
}

TEST(ProgressOverviewTest, RendersAggregatedDataWithoutReadingStorage) {
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

    // 流水统计给一组有代表性的值：今天做过、连续三天、累计十二次。
    const LearningStore::LearningStats stats{
        .attempts_today = 2, .correct_today = 7, .answered_today = 9,
        .streak_days = 3, .attempts_total = 12};
    auto* page = make_progress_overview(progress, stats);

    ASSERT_NE(page, nullptr);
    EXPECT_TRUE(page->has_css_class("progress-overview"));
    EXPECT_NE(find_label(*page, "知识点总数"), nullptr);
    // 第四张卡是「未涉及」而不是平均熟练度：被大量未开始知识点拉低的平均值
    // 既说不清学得怎么样，也指不出下一步。
    EXPECT_NE(find_label(*page, "未涉及（0 星）"), nullptr);
    EXPECT_EQ(find_label(*page, "平均熟练度"), nullptr);
    EXPECT_NE(find_frame(*page, "整体完成度"), nullptr);
    // 逐个知识点的掌握程度取代了按星级分档的直方图：后者只说得出"有几个
    // 在 3 星"，说不出是哪几个。
    EXPECT_NE(find_frame(*page, "各知识点掌握程度"), nullptr);
    EXPECT_EQ(find_frame(*page, "熟练度分布"), nullptr);

    // 章节与知识点的逐条进度不再在这里重复：它们画在学习图谱的章节卡片上。
    // 概览只留统计、建议和两张图，同一件事不给两个入口。
    EXPECT_EQ(find_expander(*page), nullptr);
    EXPECT_EQ(find_label(*page, "资源所有权"), nullptr);
}

TEST(ProgressOverviewTest, DonutReservesSpaceForItsFullStroke) {
    auto* donut = make_mastery_donut_chart(1, 2, 3);

    EXPECT_EQ(donut->get_content_width(), 230);
    EXPECT_EQ(donut->get_content_height(), 230);
}

TEST(ProgressOverviewTest, ShowsFiguresDerivedFromTheAttemptLog) {
    // 记了却不给使用者看，等于没记（仓库 ADR 0052）——这条盯住那一行有没有
    // 真的显示出来，而不是只落在库里。
    CategoryProgress progress;
    progress.total = 10;
    progress.mastered = 3;

    const LearningStore::LearningStats stats{
        .attempts_today = 2, .correct_today = 7, .answered_today = 9,
        .streak_days = 3, .attempts_total = 12};

    auto* page = make_progress_overview(progress, stats);
    ASSERT_NE(page, nullptr);

    EXPECT_NE(find_label(*page, "今天完成的考核"), nullptr);
    EXPECT_NE(find_label(*page, "7 / 9"), nullptr) << "今日答对 / 答题没显示";
    EXPECT_NE(find_label(*page, "3 天"), nullptr) << "连续日没显示";
    EXPECT_NE(find_label(*page, "12"), nullptr) << "累计次数没显示";
    EXPECT_NE(find_label(*page, "连续有记录"), nullptr);
}

} // namespace
