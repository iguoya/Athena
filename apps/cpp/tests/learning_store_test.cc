#include "storage/learning_store.h"

#include <sqlite3.h>

#include <glibmm.h>
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
    const string db_path =
        Glib::build_filename(Glib::get_tmp_dir(), "athena-learning-store-legacy-test.db");
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

// 运行历史功能已移除，但旧数据库里的表和记录属于用户数据。打开旧库时
// 不应删除或改写它；新版本只是不再读取和追加。
TEST(LearningStoreTest, KeepsLegacyRunHistoryDataUntouched) {
    const string db_path =
        Glib::build_filename(Glib::get_tmp_dir(), "athena-learning-store-run-history-legacy-test.db");
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

    {
        LearningStore store(db_path);
        EXPECT_EQ(store.load_mastery("cpp.RAII.weak"), 0);
    }

    sqlite3* verify = nullptr;
    ASSERT_EQ(sqlite3_open(db_path.c_str(), &verify), SQLITE_OK);
    sqlite3_stmt* query = nullptr;
    ASSERT_EQ(
        sqlite3_prepare_v2(
            verify,
            "SELECT output, source_hash FROM run_history WHERE function_id = ?1",
            -1,
            &query,
            nullptr),
        SQLITE_OK);
    ASSERT_EQ(
        sqlite3_bind_text(
            query, 1, "cpp.RAII.weak", -1, SQLITE_TRANSIENT),
        SQLITE_OK);
    ASSERT_EQ(sqlite3_step(query), SQLITE_ROW);
    EXPECT_STREQ(
        reinterpret_cast<const char*>(sqlite3_column_text(query, 0)),
        "旧输出");
    EXPECT_STREQ(
        reinterpret_cast<const char*>(sqlite3_column_text(query, 1)),
        "12345");
    EXPECT_EQ(sqlite3_step(query), SQLITE_DONE);
    sqlite3_finalize(query);
    sqlite3_close_v2(verify);

    std::remove(db_path.c_str());
}

TEST(LearningStoreTest, DoesNotCreateRunHistoryForNewDatabase) {
    const string db_path =
        Glib::build_filename(Glib::get_tmp_dir(), "athena-learning-store-no-run-history-test.db");
    std::remove(db_path.c_str());

    { LearningStore store(db_path); }

    sqlite3* verify = nullptr;
    ASSERT_EQ(sqlite3_open(db_path.c_str(), &verify), SQLITE_OK);
    sqlite3_stmt* query = nullptr;
    ASSERT_EQ(
        sqlite3_prepare_v2(
            verify,
            "SELECT count(*) FROM sqlite_master "
            "WHERE type = 'table' AND name = 'run_history'",
            -1,
            &query,
            nullptr),
        SQLITE_OK);
    ASSERT_EQ(sqlite3_step(query), SQLITE_ROW);
    EXPECT_EQ(sqlite3_column_int(query, 0), 0);
    sqlite3_finalize(query);
    sqlite3_close_v2(verify);

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

// “AI 讲解”缓存：没有记录时返回 nullopt，不是空 markdown——空字符串是
// 合法但没意义的讲解内容，跟"从没生成过"必须能区分开，调用方才能正确
// 判断要不要发起一次新请求。
TEST(LearningStoreTest, LoadAiInsightReturnsNulloptForUnknownKnowledgePoint) {
    const LearningStore store(":memory:");
    EXPECT_FALSE(store.load_ai_insight("cpp.RAII.weak").has_value());
}

TEST(LearningStoreTest, SavesAndReloadsAiInsight) {
    LearningStore store(":memory:");
    store.save_ai_insight(
        "cpp.RAII.weak", "void weak() { /* v1 */ }", "# 讲解 v1");

    const auto record = store.load_ai_insight("cpp.RAII.weak");
    ASSERT_TRUE(record.has_value());
    EXPECT_EQ(record->source_snapshot, "void weak() { /* v1 */ }");
    EXPECT_EQ(record->markdown, "# 讲解 v1");

    // 重复保存是 upsert，覆盖成最新一次结果，不是追加多条记录。
    store.save_ai_insight(
        "cpp.RAII.weak", "void weak() { /* v2 */ }", "# 讲解 v2");
    const auto updated = store.load_ai_insight("cpp.RAII.weak");
    ASSERT_TRUE(updated.has_value());
    EXPECT_EQ(updated->source_snapshot, "void weak() { /* v2 */ }");
    EXPECT_EQ(updated->markdown, "# 讲解 v2");
}

TEST(LearningStoreTest, KeepsAiInsightForDifferentKnowledgePointsIndependent) {
    LearningStore store(":memory:");
    store.save_ai_insight("cpp.RAII.weak", "void weak() {}", "# weak");
    store.save_ai_insight("cpp.Reference.cast", "void cast() {}", "# cast");

    EXPECT_EQ(store.load_ai_insight("cpp.RAII.weak")->markdown, "# weak");
    EXPECT_EQ(store.load_ai_insight("cpp.Reference.cast")->markdown, "# cast");
}

TEST(LearningStoreTest, DerivesStatsFromAttemptLog) {
    LearningStore db(":memory:");

    EXPECT_EQ(db.load_stats().attempts_total, 0);
    EXPECT_EQ(db.load_stats().streak_days, 0);

    db.save_assessment("cpp.ValueSemantics.copy_control", 4, 4, 5);
    db.save_assessment("cpp.ValueSemantics.rvalue", 5, 2, 2);

    const auto stats = db.load_stats();
    // 今日量与累计都来自流水；knowledge_progress 只留最新一次成绩，算不出这些。
    EXPECT_EQ(stats.attempts_total, 2);
    EXPECT_EQ(stats.attempts_today, 2);
    EXPECT_EQ(stats.correct_today, 6);
    EXPECT_EQ(stats.answered_today, 7);
    EXPECT_EQ(stats.streak_days, 1);
}

TEST(LearningStoreTest, KeepsEveryAttemptWhileMasteryIsOverwritten) {
    LearningStore db(":memory:");

    // 同一个知识点重做三次：掌握度被覆盖成最后一次，流水三条都在。
    db.save_assessment("cpp.ValueSemantics.copy_control", 2, 2, 5);
    db.save_assessment("cpp.ValueSemantics.copy_control", 3, 3, 5);
    db.save_assessment("cpp.ValueSemantics.copy_control", 5, 5, 5);

    const auto mastery = db.load_all_mastery();
    EXPECT_EQ(mastery.at("cpp.ValueSemantics.copy_control"), 5);
    EXPECT_EQ(db.load_stats().attempts_total, 3);
    EXPECT_EQ(db.load_stats().answered_today, 15);
}

} // namespace
