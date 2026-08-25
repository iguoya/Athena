#include "storage/learning_store.h"

#include <sqlite3.h>

#include <sys/stat.h>

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
    execute(
        "CREATE TABLE IF NOT EXISTS run_history ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  function_id TEXT NOT NULL,"
        "  output TEXT NOT NULL,"
        "  duration_ms REAL NOT NULL,"
        "  source_snapshot TEXT NOT NULL DEFAULT '',"
        "  git_commit TEXT NOT NULL DEFAULT '',"
        "  git_dirty INTEGER NOT NULL DEFAULT 0,"
        "  ran_at INTEGER NOT NULL)");
    migrate_legacy_run_history_columns();
    execute(
        "CREATE INDEX IF NOT EXISTS idx_run_history_function "
        "ON run_history(function_id, id DESC)");
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
    // ":memory:" 没有对应的磁盘文件，跳过。chmod 失败（比如文件系统不
    // 支持权限位）不影响数据库本身可用，不升级为异常。
    if (database_path != ":memory:") {
        chmod(database_path.c_str(), S_IRUSR | S_IWUSR);
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

void LearningStore::migrate_legacy_run_history_columns() {
    // 旧版本只存 source_hash（单向哈希，无法还原源码），也没有 git 提交
    // 信息；分别补齐缺失列即可，旧的 source_hash 列留在表里不再使用。
    if (!table_has_column(m_handle.get(), "run_history", "source_snapshot")) {
        execute(
            "ALTER TABLE run_history "
            "ADD COLUMN source_snapshot TEXT NOT NULL DEFAULT ''");
    }
    if (!table_has_column(m_handle.get(), "run_history", "git_commit")) {
        execute(
            "ALTER TABLE run_history "
            "ADD COLUMN git_commit TEXT NOT NULL DEFAULT ''");
    }
    if (!table_has_column(m_handle.get(), "run_history", "git_dirty")) {
        execute(
            "ALTER TABLE run_history "
            "ADD COLUMN git_dirty INTEGER NOT NULL DEFAULT 0");
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

void LearningStore::record_run(
    const string& function_id,
    const string& output,
    double duration_ms,
    const string& source_snapshot,
    const string& git_commit,
    bool git_dirty) {
    Statement statement(
        m_handle.get(),
        "INSERT INTO run_history"
        "(function_id, output, duration_ms, source_snapshot, git_commit, git_dirty, ran_at) "
        "VALUES(?1, ?2, ?3, ?4, ?5, ?6, ?7)");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    bind_text(m_handle.get(), statement.raw, 2, output);
    if (sqlite3_bind_double(statement.raw, 3, duration_ms) != SQLITE_OK
        || sqlite3_bind_text(statement.raw, 4, source_snapshot.c_str(), -1, SQLITE_TRANSIENT) != SQLITE_OK
        || sqlite3_bind_text(statement.raw, 5, git_commit.c_str(), -1, SQLITE_TRANSIENT) != SQLITE_OK
        || sqlite3_bind_int(statement.raw, 6, git_dirty ? 1 : 0) != SQLITE_OK
        || sqlite3_bind_int64(statement.raw, 7, unix_seconds()) != SQLITE_OK) {
        raise_sqlite_error(m_handle.get(), "bind run parameters");
    }
    if (sqlite3_step(statement.raw) != SQLITE_DONE) {
        raise_sqlite_error(m_handle.get(), "record run");
    }
}

vector<RunRecord> LearningStore::recent_runs(
    const string& function_id,
    int limit) const {
    Statement statement(
        m_handle.get(),
        "SELECT id, output, duration_ms, source_snapshot, git_commit, git_dirty, ran_at "
        "FROM run_history WHERE function_id = ?1 ORDER BY id DESC LIMIT ?2");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    if (sqlite3_bind_int(statement.raw, 2, limit) != SQLITE_OK) {
        raise_sqlite_error(m_handle.get(), "bind run limit");
    }

    vector<RunRecord> records;
    while (sqlite3_step(statement.raw) == SQLITE_ROW) {
        RunRecord record;
        record.id = sqlite3_column_int64(statement.raw, 0);
        if (const auto* output = sqlite3_column_text(statement.raw, 1)) {
            record.output = reinterpret_cast<const char*>(output);
        }
        record.duration_ms = sqlite3_column_double(statement.raw, 2);
        if (const auto* snapshot = sqlite3_column_text(statement.raw, 3)) {
            record.source_snapshot = reinterpret_cast<const char*>(snapshot);
        }
        if (const auto* commit = sqlite3_column_text(statement.raw, 4)) {
            record.git_commit = reinterpret_cast<const char*>(commit);
        }
        record.git_dirty = sqlite3_column_int(statement.raw, 5) != 0;
        record.ran_at = sqlite3_column_int64(statement.raw, 6);
        records.push_back(std::move(record));
    }
    return records;
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
