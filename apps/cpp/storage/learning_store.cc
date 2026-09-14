#include "storage/learning_store.h"

#include <glib/gstdio.h>
#include <sqlite3.h>

#include <chrono>
#include <stdexcept>

using namespace std;

namespace {

long long unix_seconds() {
    return chrono::duration_cast<chrono::seconds>(
               chrono::system_clock::now().time_since_epoch())
        .count();
}

[[noreturn]] void raise_sqlite_error(sqlite3* handle, const string& action) {
    throw runtime_error(
        "learning store failed to " + action + ": " + sqlite3_errmsg(handle));
}

struct Statement {
    sqlite3_stmt* raw = nullptr;

    explicit Statement(sqlite3* handle, const string& sql) {
        if (sqlite3_prepare_v2(handle, sql.c_str(), -1, &raw, nullptr)
            != SQLITE_OK) {
            raise_sqlite_error(handle, "prepare statement: " + sql);
        }
    }

    ~Statement() { sqlite3_finalize(raw); }

    Statement(const Statement&) = delete;
    Statement& operator=(const Statement&) = delete;
};

void bind_text(sqlite3* handle, sqlite3_stmt* statement, int index, const string& value) {
    if (sqlite3_bind_text(statement, index, value.c_str(), -1, SQLITE_TRANSIENT)
        != SQLITE_OK) {
        raise_sqlite_error(handle, "bind text parameter");
    }
}

bool table_has_column(sqlite3* handle, const string& table, const string& column) {
    Statement info(handle, "PRAGMA table_info(" + table + ")");
    while (sqlite3_step(info.raw) == SQLITE_ROW) {
        const auto* name =
            reinterpret_cast<const char*>(sqlite3_column_text(info.raw, 1));
        if (name && column == name) {
            return true;
        }
    }
    return false;
}

} // namespace

LearningStore::LearningStore(const string& database_path) {
    sqlite3* raw = nullptr;
    if (sqlite3_open(database_path.c_str(), &raw) != SQLITE_OK) {
        const string message = raw ? sqlite3_errmsg(raw) : "unknown error";
        sqlite3_close_v2(raw);
        throw runtime_error("learning store failed to open " + database_path + ": " + message);
    }
    m_handle.reset(raw);

    execute(
        "CREATE TABLE IF NOT EXISTS knowledge_progress ("
        "  function_id TEXT PRIMARY KEY,"
        "  mastery INTEGER NOT NULL DEFAULT 0,"
        "  updated_at INTEGER NOT NULL DEFAULT 0)");
    migrate_legacy_status_column();
    migrate_assessment_columns();
    execute(
        "CREATE TABLE IF NOT EXISTS app_settings ("
        "  key TEXT PRIMARY KEY,"
        "  value TEXT NOT NULL)");
    execute(
        "CREATE TABLE IF NOT EXISTS ai_insight ("
        "  function_id TEXT PRIMARY KEY,"
        "  source_snapshot TEXT NOT NULL DEFAULT '',"
        "  markdown TEXT NOT NULL DEFAULT '',"
        "  generated_at INTEGER NOT NULL DEFAULT 0)");

    // 数据库可能存有 AI 服务商 Key 这类敏感配置；收紧到仅当前用户可读写，
    // 挡住最基础的意外泄露（同机其他账户、被囫囵打进备份/同步）。
    // ":memory:" 没有对应的磁盘文件，跳过。失败（文件系统不支持权限位、
    // 或 Windows 上只有只读标志可设）不影响数据库本身可用，不升级为异常。
    // 用 GLib 的 g_chmod 而不是 POSIX 的 chmod：后者在 Windows 上不存在
    // （ADR 0047）；权限位直接写八进制，避开 S_IRUSR 这些 POSIX 宏。
    if (database_path != ":memory:") {
        g_chmod(database_path.c_str(), 0600);
    }
}

// 记录最近一次评定的原始成绩。只存 mastery 的话，界面上只能显示一个星级，
// 看不出"这 5 星是 8 题全对还是 2 题蒙对的"——考核结果要能查得到才有说服力。
void LearningStore::migrate_assessment_columns() {
    if (!table_has_column(m_handle.get(), "knowledge_progress", "last_correct")) {
        execute(
            "ALTER TABLE knowledge_progress "
            "ADD COLUMN last_correct INTEGER NOT NULL DEFAULT 0");
    }
    if (!table_has_column(m_handle.get(), "knowledge_progress", "last_total")) {
        execute(
            "ALTER TABLE knowledge_progress "
            "ADD COLUMN last_total INTEGER NOT NULL DEFAULT 0");
    }
}

void LearningStore::migrate_legacy_status_column() {
    const bool has_status =
        table_has_column(m_handle.get(), "knowledge_progress", "status");
    const bool had_mastery =
        table_has_column(m_handle.get(), "knowledge_progress", "mastery");

    if (!had_mastery) {
        execute(
            "ALTER TABLE knowledge_progress "
            "ADD COLUMN mastery INTEGER NOT NULL DEFAULT 0");
    }
    if (has_status && !had_mastery) {
        // 旧版本以位标志持久化（bit0 已理解、bit1 已掌握）；折算成掌握程度星级，
        // 避免旧库升级后直接丢弃已记录的学习进度。
        execute(
            "UPDATE knowledge_progress SET mastery = "
            "  CASE WHEN (status & 3) = 3 THEN 5 "
            "       WHEN (status & 2) = 2 THEN 3 "
            "       WHEN (status & 1) = 1 THEN 1 "
            "       ELSE 0 END");
    }
}

LearningStore::~LearningStore() = default;

void LearningStore::Sqlite3Deleter::operator()(sqlite3* handle) const noexcept {
    sqlite3_close_v2(handle);
}

void LearningStore::execute(const string& sql) const {
    char* message = nullptr;
    if (sqlite3_exec(m_handle.get(), sql.c_str(), nullptr, nullptr, &message)
        != SQLITE_OK) {
        const string detail = message ? message : "unknown error";
        sqlite3_free(message);
        throw runtime_error("learning store failed to execute: " + detail);
    }
}

int LearningStore::load_mastery(const string& function_id) const {
    Statement statement(
        m_handle.get(),
        "SELECT mastery FROM knowledge_progress "
        "WHERE function_id = ?1");
    bind_text(m_handle.get(), statement.raw, 1, function_id);

    if (sqlite3_step(statement.raw) == SQLITE_ROW) {
        return sqlite3_column_int(statement.raw, 0);
    }
    return 0;
}

void LearningStore::save_mastery(const string& function_id, int mastery) {
    Statement statement(
        m_handle.get(),
        "INSERT INTO knowledge_progress(function_id, mastery, updated_at) "
        "VALUES(?1, ?2, ?3) "
        "ON CONFLICT(function_id) DO UPDATE SET "
        "  mastery = excluded.mastery,"
        "  updated_at = excluded.updated_at");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    if (sqlite3_bind_int(statement.raw, 2, mastery) != SQLITE_OK
        || sqlite3_bind_int64(statement.raw, 3, unix_seconds()) != SQLITE_OK) {
        raise_sqlite_error(m_handle.get(), "bind progress parameters");
    }
    if (sqlite3_step(statement.raw) != SQLITE_DONE) {
        raise_sqlite_error(m_handle.get(), "save progress");
    }
}

void LearningStore::save_assessment(
    const string& function_id, int mastery, int correct, int total) {
    Statement statement(
        m_handle.get(),
        "INSERT INTO knowledge_progress"
        "(function_id, mastery, last_correct, last_total, updated_at) "
        "VALUES(?1, ?2, ?3, ?4, ?5) "
        "ON CONFLICT(function_id) DO UPDATE SET "
        "  mastery = excluded.mastery,"
        "  last_correct = excluded.last_correct,"
        "  last_total = excluded.last_total,"
        "  updated_at = excluded.updated_at");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    if (sqlite3_bind_int(statement.raw, 2, mastery) != SQLITE_OK
        || sqlite3_bind_int(statement.raw, 3, correct) != SQLITE_OK
        || sqlite3_bind_int(statement.raw, 4, total) != SQLITE_OK
        || sqlite3_bind_int64(statement.raw, 5, unix_seconds()) != SQLITE_OK) {
        raise_sqlite_error(m_handle.get(), "bind assessment parameters");
    }
    if (sqlite3_step(statement.raw) != SQLITE_DONE) {
        raise_sqlite_error(m_handle.get(), "save assessment");
    }
}

LearningStore::Assessment LearningStore::load_assessment(
    const string& function_id) const {
    Statement statement(
        m_handle.get(),
        "SELECT mastery, last_correct, last_total, updated_at "
        "FROM knowledge_progress WHERE function_id = ?1");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    if (sqlite3_step(statement.raw) == SQLITE_ROW) {
        return Assessment{
            .mastery = sqlite3_column_int(statement.raw, 0),
            .correct = sqlite3_column_int(statement.raw, 1),
            .total = sqlite3_column_int(statement.raw, 2),
            .updated_at = sqlite3_column_int64(statement.raw, 3),
        };
    }
    return {};
}

map<string, LearningStore::Assessment> LearningStore::load_all_assessments()
    const {
    Statement statement(
        m_handle.get(),
        "SELECT function_id, mastery, last_correct, last_total, updated_at "
        "FROM knowledge_progress");
    map<string, Assessment> result;
    while (sqlite3_step(statement.raw) == SQLITE_ROW) {
        const auto* id =
            reinterpret_cast<const char*>(sqlite3_column_text(statement.raw, 0));
        if (!id) {
            continue;
        }
        result[id] = Assessment{
            .mastery = sqlite3_column_int(statement.raw, 1),
            .correct = sqlite3_column_int(statement.raw, 2),
            .total = sqlite3_column_int(statement.raw, 3),
            .updated_at = sqlite3_column_int64(statement.raw, 4),
        };
    }
    return result;
}

map<string, int> LearningStore::load_all_mastery() const {
    Statement statement(
        m_handle.get(),
        "SELECT function_id, mastery FROM knowledge_progress");

    map<string, int> mastery_by_id;
    while (sqlite3_step(statement.raw) == SQLITE_ROW) {
        if (const auto* function_id = sqlite3_column_text(statement.raw, 0)) {
            mastery_by_id[reinterpret_cast<const char*>(function_id)] =
                sqlite3_column_int(statement.raw, 1);
        }
    }
    return mastery_by_id;
}

optional<AiInsightRecord> LearningStore::load_ai_insight(
    const string& function_id) const {
    Statement statement(
        m_handle.get(),
        "SELECT source_snapshot, markdown FROM ai_insight WHERE function_id = ?1");
    bind_text(m_handle.get(), statement.raw, 1, function_id);

    if (sqlite3_step(statement.raw) != SQLITE_ROW) {
        return nullopt;
    }
    AiInsightRecord record;
    if (const auto* snapshot = sqlite3_column_text(statement.raw, 0)) {
        record.source_snapshot = reinterpret_cast<const char*>(snapshot);
    }
    if (const auto* markdown = sqlite3_column_text(statement.raw, 1)) {
        record.markdown = reinterpret_cast<const char*>(markdown);
    }
    return record;
}

void LearningStore::save_ai_insight(
    const string& function_id,
    const string& source_snapshot,
    const string& markdown) {
    Statement statement(
        m_handle.get(),
        "INSERT INTO ai_insight(function_id, source_snapshot, markdown, generated_at) "
        "VALUES(?1, ?2, ?3, ?4) "
        "ON CONFLICT(function_id) DO UPDATE SET "
        "  source_snapshot = excluded.source_snapshot,"
        "  markdown = excluded.markdown,"
        "  generated_at = excluded.generated_at");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    bind_text(m_handle.get(), statement.raw, 2, source_snapshot);
    bind_text(m_handle.get(), statement.raw, 3, markdown);
    if (sqlite3_bind_int64(statement.raw, 4, unix_seconds()) != SQLITE_OK) {
        raise_sqlite_error(m_handle.get(), "bind ai insight timestamp");
    }
    if (sqlite3_step(statement.raw) != SQLITE_DONE) {
        raise_sqlite_error(m_handle.get(), "save ai insight");
    }
}

string LearningStore::get_setting(const string& key) const {
    Statement statement(
        m_handle.get(), "SELECT value FROM app_settings WHERE key = ?1");
    bind_text(m_handle.get(), statement.raw, 1, key);

    string value;
    if (sqlite3_step(statement.raw) == SQLITE_ROW) {
        if (const auto* text = sqlite3_column_text(statement.raw, 0)) {
            value = reinterpret_cast<const char*>(text);
        }
    }
    return value;
}

void LearningStore::set_setting(const string& key, const string& value) {
    if (value.empty()) {
        Statement statement(
            m_handle.get(), "DELETE FROM app_settings WHERE key = ?1");
        bind_text(m_handle.get(), statement.raw, 1, key);
        if (sqlite3_step(statement.raw) != SQLITE_DONE) {
            raise_sqlite_error(m_handle.get(), "clear setting");
        }
        return;
    }

    Statement statement(
        m_handle.get(),
        "INSERT INTO app_settings(key, value) VALUES(?1, ?2) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value");
    bind_text(m_handle.get(), statement.raw, 1, key);
    bind_text(m_handle.get(), statement.raw, 2, value);
    if (sqlite3_step(statement.raw) != SQLITE_DONE) {
        raise_sqlite_error(m_handle.get(), "save setting");
    }
}
