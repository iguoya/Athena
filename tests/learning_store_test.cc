#include "storage/learning_store.h"

#include <sqlite3.h>

#include <gtest/gtest.h>

#include <cstdio>
#include <stdexcept>

namespace {

TEST(LearningStoreTest, ReturnsDefaultMasteryForUnknownKnowledgePoint) {
    const LearningStore store(":memory:");
    EXPECT_EQ(store.load_mastery("cpp.Reference.reference_basics"), 0);
}

TEST(LearningStoreTest, SavesAndReloadsMastery) {
    LearningStore store(":memory:");
    store.save_mastery("cpp.RAII.weak", 2);
    EXPECT_EQ(store.load_mastery("cpp.RAII.weak"), 2);

    store.save_mastery("cpp.RAII.weak", 5);
    EXPECT_EQ(store.load_mastery("cpp.RAII.weak"), 5);
}

TEST(LearningStoreTest, KeepsDifferentKnowledgePointsIndependent) {
    LearningStore store(":memory:");
    store.save_mastery("cpp.RAII.weak", 1);
    store.save_mastery("cpp.Reference.cast", 4);

    EXPECT_EQ(store.load_mastery("cpp.RAII.weak"), 1);
    EXPECT_EQ(store.load_mastery("cpp.Reference.cast"), 4);
}

TEST(LearningStoreTest, ReturnsMostRecentRunsFirst) {
    LearningStore store(":memory:");
    store.record_run(
        "cpp.RAII.unique", "first", 10.0, "void unique() { /* v1 */ }", "a1b2c3d", false);
    store.record_run(
        "cpp.RAII.unique", "second", 20.5, "void unique() { /* v2 */ }", "e4f5g6h", true);
    store.record_run("cpp.Reference.cast", "other", 1.0, "void cast() {}", "", false);

    const auto runs = store.recent_runs("cpp.RAII.unique", 10);
    ASSERT_EQ(runs.size(), 2u);
    EXPECT_EQ(runs.front().output, "second");
    EXPECT_DOUBLE_EQ(runs.front().duration_ms, 20.5);
    EXPECT_EQ(runs.front().source_snapshot, "void unique() { /* v2 */ }");
    EXPECT_EQ(runs.front().git_commit, "e4f5g6h");
    EXPECT_TRUE(runs.front().git_dirty);
    EXPECT_EQ(runs.back().output, "first");
    EXPECT_EQ(runs.back().git_commit, "a1b2c3d");
    EXPECT_FALSE(runs.back().git_dirty);

    EXPECT_EQ(store.recent_runs("cpp.Reference.cast", 10).size(), 1u);
}

TEST(LearningStoreTest, RejectsInvalidDatabasePath) {
    EXPECT_THROW(
        LearningStore("/nonexistent-directory/athena.db"),
        runtime_error);
}

// 复现旧版本升级场景：旧库的 knowledge_progress 只有位标志 status 列
// （bit0 已理解、bit1 已掌握），没有 mastery。CREATE TABLE IF NOT EXISTS
// 对已存在的表是空操作，必须显式迁移，否则后续查询会因
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
    EXPECT_EQ(store.load_mastery("cpp.RAII.weak"), 5);
    EXPECT_EQ(store.load_mastery("cpp.RAII.unique"), 3);
    EXPECT_EQ(store.load_mastery("cpp.Reference.cast"), 1);
    EXPECT_EQ(store.load_mastery("cpp.Reference.const"), 0);

    // 笔记功能已从界面和运行时 API 移除，但升级和重新评分不能覆盖旧数据。
    store.save_mastery("cpp.RAII.weak", 4);
    sqlite3* verify = nullptr;
    ASSERT_EQ(sqlite3_open(db_path.c_str(), &verify), SQLITE_OK);
    sqlite3_stmt* note_query = nullptr;
    ASSERT_EQ(
        sqlite3_prepare_v2(
            verify,
            "SELECT note FROM knowledge_progress WHERE function_id = ?1",
            -1,
            &note_query,
            nullptr),
        SQLITE_OK);
    ASSERT_EQ(
        sqlite3_bind_text(
            note_query, 1, "cpp.RAII.weak", -1, SQLITE_TRANSIENT),
        SQLITE_OK);
    ASSERT_EQ(sqlite3_step(note_query), SQLITE_ROW);
    EXPECT_STREQ(
        reinterpret_cast<const char*>(sqlite3_column_text(note_query, 0)),
        "已理解并掌握");
    sqlite3_finalize(note_query);
    sqlite3_close_v2(verify);

    std::remove(db_path.c_str());
}

// 复现 run_history 的旧结构：只存 source_hash（单向哈希），没有
// source_snapshot。升级后旧记录的快照读出来应该是空字符串（哈希无法
// 还原源码），不应抛异常，新记录正常写入 source_snapshot。
TEST(LearningStoreTest, MigratesLegacyRunHistoryColumnOnUpgrade) {
    const string db_path = "/tmp/athena-learning-store-run-history-legacy-test.db";
    std::remove(db_path.c_str());

    sqlite3* legacy = nullptr;
    ASSERT_EQ(sqlite3_open(db_path.c_str(), &legacy), SQLITE_OK);
    ASSERT_EQ(
        sqlite3_exec(
            legacy,
            "CREATE TABLE run_history ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  function_id TEXT NOT NULL,"
            "  output TEXT NOT NULL,"
            "  duration_ms REAL NOT NULL,"
            "  source_hash TEXT NOT NULL DEFAULT '',"
            "  ran_at INTEGER NOT NULL);"
            "INSERT INTO run_history(function_id, output, duration_ms, source_hash, ran_at) "
            "VALUES ('cpp.RAII.weak', '旧输出', 5.0, '12345', 100);",
            nullptr,
            nullptr,
            nullptr),
        SQLITE_OK);
    sqlite3_close_v2(legacy);

    LearningStore store(db_path);
    const auto old_runs = store.recent_runs("cpp.RAII.weak", 10);
    ASSERT_EQ(old_runs.size(), 1u);
    EXPECT_EQ(old_runs.front().output, "旧输出");
    EXPECT_EQ(old_runs.front().source_snapshot, "");
    EXPECT_EQ(old_runs.front().git_commit, "");
    EXPECT_FALSE(old_runs.front().git_dirty);

    store.record_run(
        "cpp.RAII.weak", "新输出", 8.0, "void weak() { /* new */ }", "a1b2c3d", false);
    const auto runs = store.recent_runs("cpp.RAII.weak", 10);
    ASSERT_EQ(runs.size(), 2u);
    EXPECT_EQ(runs.front().output, "新输出");
    EXPECT_EQ(runs.front().git_commit, "a1b2c3d");
    EXPECT_EQ(runs.front().source_snapshot, "void weak() { /* new */ }");

    std::remove(db_path.c_str());
}

// 学习进度统计页靠这一个查询拿到全部熟练度：只应返回有过记录的知识点，
// 从没评过星的知识点不出现在结果里（由调用方按 0 处理），否则统计会把
// 未开始的也算成"学习中"。
TEST(LearningStoreTest, LoadAllMasteryReturnsOnlyRecordedEntries) {
    LearningStore store(":memory:");
    EXPECT_TRUE(store.load_all_mastery().empty());

    store.save_mastery("cpp.Reference.reference_basics", 5);
    store.save_mastery("cpp.Reference.const_reference", 2);
    store.save_mastery("cpp.RAII.raii_basic", 0);

    const auto mastery = store.load_all_mastery();
    EXPECT_EQ(mastery.size(), 3u);
    EXPECT_EQ(mastery.at("cpp.Reference.reference_basics"), 5);
    EXPECT_EQ(mastery.at("cpp.Reference.const_reference"), 2);
    EXPECT_EQ(mastery.at("cpp.RAII.raii_basic"), 0);
    EXPECT_EQ(mastery.count("cpp.RAII.never_rated"), 0u);

    // 重复评分走的是 upsert，不应该出现同一个 function_id 两条记录。
    store.save_mastery("cpp.Reference.const_reference", 4);
    const auto updated = store.load_all_mastery();
    EXPECT_EQ(updated.size(), 3u);
    EXPECT_EQ(updated.at("cpp.Reference.const_reference"), 4);
}

// AI 服务商 Key 走这组通用 key-value 设置存取；未配置时返回空串，调用方
// 按"未配置"处理，不应该抛异常或返回哨兵值。
TEST(LearningStoreTest, GetSettingReturnsEmptyForUnknownKey) {
    LearningStore store(":memory:");
    EXPECT_EQ(store.get_setting("ai_provider_key_ark"), "");
}

TEST(LearningStoreTest, SetSettingPersistsAndOverwrites) {
    LearningStore store(":memory:");
    store.set_setting("ai_provider_key_ark", "ark-first");
    EXPECT_EQ(store.get_setting("ai_provider_key_ark"), "ark-first");

    // 重复写入是 upsert，不产生第二行。
    store.set_setting("ai_provider_key_ark", "ark-second");
    EXPECT_EQ(store.get_setting("ai_provider_key_ark"), "ark-second");
}

TEST(LearningStoreTest, SetSettingKeepsDifferentKeysIndependent) {
    LearningStore store(":memory:");
    store.set_setting("ai_provider_key_ark", "ark-value");
    store.set_setting("ai_provider_key_deepseek", "deepseek-value");

    EXPECT_EQ(store.get_setting("ai_provider_key_ark"), "ark-value");
    EXPECT_EQ(store.get_setting("ai_provider_key_deepseek"), "deepseek-value");
}

// 传空串等价于清除这条设置（DELETE），不是留一行空值——否则"曾经配置过
// 又清空"和"从没配置过"在 get_setting 的返回值上无法区分，但两者本该
// 一样按"未配置"处理，用 DELETE 直接消掉这个歧义源头。
TEST(LearningStoreTest, SetSettingWithEmptyValueClearsIt) {
    LearningStore store(":memory:");
    store.set_setting("ai_provider_key_ark", "ark-value");
    ASSERT_EQ(store.get_setting("ai_provider_key_ark"), "ark-value");

    store.set_setting("ai_provider_key_ark", "");
    EXPECT_EQ(store.get_setting("ai_provider_key_ark"), "");
}

} // namespace
