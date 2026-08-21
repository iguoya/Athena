#include "registry/progress_stats.h"

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

namespace {

// 两章：Alpha 有 3 个知识点，Beta 有 2 个；Empty 没有知识点，应当整章跳过。
ChapterCatalog MakeCatalog() {
    using json = nlohmann::json;
    const json icon = {{"type", "theme"}, {"name", "test"}, {"path", ""}};
    auto make_point = [&icon](
                          const string& chapter,
                          const string& name,
                          const string& title) {
        return json{
            {"function_id", "cpp." + chapter + "." + name},
            {"name", name},
            {"title", title},
            {"description", "d"},
            {"group", ""},
            {"source", ""},
            {"importance", 0},
            {"icon", icon},
        };
    };
    auto make_chapter = [&icon](
                            const string& name,
                            const string& title,
                            json subchapters) {
        return json{
            {"name", name},
            {"title", title},
            {"description", "测试章节"},
            {"overview_document", ""},
            {"resource_path", "/app/chapters/code.ui"},
            {"widget_name", "chapter_page"},
            {"source", ""},
            {"implementation_header", ""},
            {"icon", icon},
            {"groups", json::array()},
            {"subchapters", std::move(subchapters)},
        };
    };

    const json source = {
        {"catalog_version", 1},
        {"categories", json::array({
            {
                {"name", "cpp"},
                {"title", "C++"},
                {"description", "测试用分类"},
                {"icon", icon},
                {"handbook_documents", json::array()},
                {"chapters", json::array({
                    make_chapter("Empty", "无知识点章节", json::array()),
                    make_chapter("Alpha", "甲章", json::array({
                        make_point("Alpha", "one", "知识点一"),
                        make_point("Alpha", "two", "知识点二"),
                        make_point("Alpha", "three", "知识点三"),
                    })),
                    make_chapter("Beta", "乙章", json::array({
                        make_point("Beta", "four", "知识点四"),
                        make_point("Beta", "five", "知识点五"),
                    })),
                })},
            },
        })},
    };
    return ChapterCatalog::from_runtime_json(source.dump());
}

TEST(ProgressStatsTest, CrossesCatalogWithRecordedMastery) {
    const auto catalog = MakeCatalog();
    const map<string, int> mastery = {
        {"cpp.Alpha.one", 5},
        {"cpp.Alpha.two", 3},
        // Alpha.three 没有记录，按 0 处理
        {"cpp.Beta.four", 0},
        {"cpp.Beta.five", 4},
    };

    const auto progress = aggregate_category_progress(catalog, "cpp", mastery);

    // 没有知识点的章节不进结果，也不计入总数。
    ASSERT_EQ(progress.chapters.size(), 2u);
    EXPECT_EQ(progress.chapters[0].chapter_title, "甲章");
    EXPECT_EQ(progress.chapters[1].chapter_title, "乙章");

    EXPECT_EQ(progress.total, 5);
    EXPECT_EQ(progress.mastered, 1);     // 只有 5 星算已掌握
    EXPECT_EQ(progress.in_progress, 2);  // 3 星和 4 星
    EXPECT_EQ(progress.not_started, 2);  // 0 星 + 无记录
    EXPECT_EQ(progress.mastery_sum, 12);
    EXPECT_DOUBLE_EQ(progress.average_mastery(), 12.0 / 5.0);
}

// 完成度必须是平均熟练度占满分的比例，不是"5 星占比"：否则没有任何
// 5 星时章节进度条会恒为 0，无法反映 1-4 星的学习进展。
TEST(ProgressStatsTest, CompletionRatioUsesAverageMasteryNotFiveStarCount) {
    const auto catalog = MakeCatalog();
    const map<string, int> mastery = {
        {"cpp.Alpha.one", 4},
        {"cpp.Alpha.two", 4},
        {"cpp.Alpha.three", 4},
    };

    const auto progress = aggregate_category_progress(catalog, "cpp", mastery);
    const auto& alpha = progress.chapters[0];

    EXPECT_EQ(alpha.mastered, 0);
    EXPECT_GT(alpha.completion_ratio(), 0.0);
    EXPECT_DOUBLE_EQ(alpha.completion_ratio(), 12.0 / 15.0);
}

TEST(ProgressStatsTest, HistogramCountsEveryKnowledgePointOnce) {
    const auto catalog = MakeCatalog();
    const map<string, int> mastery = {
        {"cpp.Alpha.one", 5},
        {"cpp.Alpha.two", 5},
        {"cpp.Alpha.three", 2},
        {"cpp.Beta.five", 2},
    };

    const auto histogram =
        aggregate_category_progress(catalog, "cpp", mastery).mastery_histogram();

    EXPECT_EQ(histogram[0], 1);  // Beta.four 无记录
    EXPECT_EQ(histogram[1], 0);
    EXPECT_EQ(histogram[2], 2);
    EXPECT_EQ(histogram[3], 0);
    EXPECT_EQ(histogram[4], 0);
    EXPECT_EQ(histogram[5], 2);

    int sum = 0;
    for (const int count : histogram) {
        sum += count;
    }
    EXPECT_EQ(sum, 5);
}

// 存储层没有 CHECK 约束，越界的熟练度不应该越界写直方图数组。
TEST(ProgressStatsTest, HistogramClampsOutOfRangeMastery) {
    const auto catalog = MakeCatalog();
    const map<string, int> mastery = {
        {"cpp.Alpha.one", 99},
        {"cpp.Alpha.two", -7},
    };

    const auto histogram =
        aggregate_category_progress(catalog, "cpp", mastery).mastery_histogram();

    EXPECT_EQ(histogram[kMaxMastery], 1);
    EXPECT_EQ(histogram[0], 4);  // -7 夹到 0，另外 3 个无记录
}

TEST(ProgressStatsTest, UnknownCategoryYieldsEmptyProgress) {
    const auto catalog = MakeCatalog();
    const auto progress = aggregate_category_progress(catalog, "no_such", {});

    EXPECT_TRUE(progress.chapters.empty());
    EXPECT_EQ(progress.total, 0);
    EXPECT_DOUBLE_EQ(progress.average_mastery(), 0.0);
}

TEST(ProgressStatsTest, EmptyMasteryMapTreatsEverythingAsNotStarted) {
    const auto catalog = MakeCatalog();
    const auto progress = aggregate_category_progress(catalog, "cpp", {});

    EXPECT_EQ(progress.total, 5);
    EXPECT_EQ(progress.mastered, 0);
    EXPECT_EQ(progress.in_progress, 0);
    EXPECT_EQ(progress.not_started, 5);
    EXPECT_DOUBLE_EQ(progress.chapters[0].completion_ratio(), 0.0);
}

} // namespace
