#include "storage/learning_store.h"

#include <sqlite3.h>

#include <gtest/gtest.h>

#include <cstdio>
#include <stdexcept>

namespace {

TEST(LearningStoreTest, ReturnsDefaultProgressForUnknownKnowledgePoint) {
    const LearningStore store(":memory:");
    const auto progress = store.load_progress("cpp.Reference.reference_basics");

    EXPECT_EQ(progress.importance, 0);
    EXPECT_EQ(progress.mastery, 0);
    EXPECT_EQ(progress.note, "");
}

TEST(LearningStoreTest, SavesAndReloadsProgress) {
    LearningStore store(":memory:");
    store.save_progress("cpp.RAII.weak", 3, 2, "循环引用要用 weak_ptr 打破");

    const auto progress = store.load_progress("cpp.RAII.weak");
    EXPECT_EQ(progress.importance, 3);
    EXPECT_EQ(progress.mastery, 2);
    EXPECT_EQ(progress.note, "循环引用要用 weak_ptr 打破");
    EXPECT_GT(progress.updated_at, 0);

    store.save_progress("cpp.RAII.weak", 3, 5, "已掌握");
    const auto updated = store.load_progress("cpp.RAII.weak");
    EXPECT_EQ(updated.importance, 3);
    EXPECT_EQ(updated.mastery, 5);
    EXPECT_EQ(updated.note, "已掌握");
}

TEST(LearningStoreTest, KeepsDifferentKnowledgePointsIndependent) {
    LearningStore store(":memory:");
    store.save_progress("cpp.RAII.weak", 2, 1, "weak");
    store.save_progress("cpp.Reference.cast", 1, 4, "cast");

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

// 复现旧版本升级场景：旧库的 knowledge_progress 只有位标志 status 列
// （bit0 已理解、bit1 已掌握），没有 importance/mastery。CREATE TABLE
// IF NOT EXISTS 对已存在的表是空操作，必须显式迁移，否则后续查询会因
// "no such column" 抛出异常。
TEST(LearningStoreTest, MigratesLegacyStatusColumnOnUpgrade) {
    const string db_path = "/tmp/athena-learning-store-legacy-test.db";
    std::remove(db_path.c_str());

    sqlite3* legacy = nullptr;
    ASSERT_EQ(sqlite3_open(db_path.c_str(), &legacy), SQLITE_OK);
    ASSERT_EQ(
        sqlite3_exec(
            legacy,
            "CREATE TABLE knowledge_progress ("
            "  function_id TEXT PRIMARY KEY,"
            "  status INTEGER NOT NULL DEFAULT 0,"
            "  note TEXT NOT NULL DEFAULT '',"
            "  updated_at INTEGER NOT NULL DEFAULT 0);"
            "INSERT INTO knowledge_progress(function_id, status, note, updated_at) "
            "VALUES"
            "  ('cpp.RAII.weak', 3, '已理解并掌握', 100),"
            "  ('cpp.RAII.unique', 2, '仅掌握', 100),"
            "  ('cpp.Reference.cast', 1, '仅理解', 100),"
            "  ('cpp.Reference.const', 0, '都没标', 100);",
            nullptr,
            nullptr,
            nullptr),
        SQLITE_OK);
    sqlite3_close_v2(legacy);

    // 打开旧库不应抛异常，且应能立即按新字段查询——这正是升级后崩溃的场景。
    LearningStore store(db_path);
    EXPECT_EQ(store.load_progress("cpp.RAII.weak").mastery, 5);
    EXPECT_EQ(store.load_progress("cpp.RAII.unique").mastery, 3);
    EXPECT_EQ(store.load_progress("cpp.Reference.cast").mastery, 1);
    EXPECT_EQ(store.load_progress("cpp.Reference.const").mastery, 0);
    EXPECT_EQ(store.load_progress("cpp.RAII.weak").note, "已理解并掌握");

    std::remove(db_path.c_str());
}

} // namespace
