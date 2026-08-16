#include "storage/learning_store.h"

#include <gtest/gtest.h>

#include <stdexcept>

namespace {

TEST(LearningStoreTest, ReturnsDefaultProgressForUnknownKnowledgePoint) {
    const LearningStore store(":memory:");
    const auto progress = store.load_progress("cpp.Reference.reference_basics");

    EXPECT_EQ(progress.status, 0);
    EXPECT_EQ(progress.note, "");
}

TEST(LearningStoreTest, SavesAndReloadsProgress) {
    LearningStore store(":memory:");
    store.save_progress("cpp.RAII.weak", 2, "循环引用要用 weak_ptr 打破");

    const auto progress = store.load_progress("cpp.RAII.weak");
    EXPECT_EQ(progress.status, 2);
    EXPECT_EQ(progress.note, "循环引用要用 weak_ptr 打破");
    EXPECT_GT(progress.updated_at, 0);

    store.save_progress("cpp.RAII.weak", 1, "已掌握");
    const auto updated = store.load_progress("cpp.RAII.weak");
    EXPECT_EQ(updated.status, 1);
    EXPECT_EQ(updated.note, "已掌握");
}

TEST(LearningStoreTest, KeepsDifferentKnowledgePointsIndependent) {
    LearningStore store(":memory:");
    store.save_progress("cpp.RAII.weak", 2, "weak");
    store.save_progress("cpp.Reference.cast", 1, "cast");

    EXPECT_EQ(store.load_progress("cpp.RAII.weak").note, "weak");
    EXPECT_EQ(store.load_progress("cpp.Reference.cast").note, "cast");
}

TEST(LearningStoreTest, ReturnsMostRecentRunsFirst) {
    LearningStore store(":memory:");
    store.record_run("cpp.RAII.unique", "first", 10.0, "hash-a");
    store.record_run("cpp.RAII.unique", "second", 20.5, "hash-b");
    store.record_run("cpp.Reference.cast", "other", 1.0, "hash-c");

    const auto runs = store.recent_runs("cpp.RAII.unique", 10);
    ASSERT_EQ(runs.size(), 2u);
    EXPECT_EQ(runs.front().output, "second");
    EXPECT_DOUBLE_EQ(runs.front().duration_ms, 20.5);
    EXPECT_EQ(runs.front().source_hash, "hash-b");
    EXPECT_EQ(runs.back().output, "first");

    EXPECT_EQ(store.recent_runs("cpp.Reference.cast", 10).size(), 1u);
}

TEST(LearningStoreTest, RejectsInvalidDatabasePath) {
    EXPECT_THROW(
        LearningStore("/nonexistent-directory/athena.db"),
        runtime_error);
}

} // namespace
