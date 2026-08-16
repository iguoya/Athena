#include "storage/learning_store.h"

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
        "  importance INTEGER NOT NULL DEFAULT 0,"
        "  mastery INTEGER NOT NULL DEFAULT 0,"
        "  note TEXT NOT NULL DEFAULT '',"
        "  updated_at INTEGER NOT NULL DEFAULT 0)");
    execute(
        "CREATE TABLE IF NOT EXISTS run_history ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  function_id TEXT NOT NULL,"
        "  output TEXT NOT NULL,"
        "  duration_ms REAL NOT NULL,"
        "  source_hash TEXT NOT NULL DEFAULT '',"
        "  ran_at INTEGER NOT NULL)");
    execute(
        "CREATE INDEX IF NOT EXISTS idx_run_history_function "
        "ON run_history(function_id, id DESC)");
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

KnowledgeProgress LearningStore::load_progress(const string& function_id) const {
    Statement statement(
        m_handle.get(),
        "SELECT importance, mastery, note, updated_at FROM knowledge_progress "
        "WHERE function_id = ?1");
    bind_text(m_handle.get(), statement.raw, 1, function_id);

    KnowledgeProgress progress;
    if (sqlite3_step(statement.raw) == SQLITE_ROW) {
        progress.importance = sqlite3_column_int(statement.raw, 0);
        progress.mastery = sqlite3_column_int(statement.raw, 1);
        if (const auto* note = sqlite3_column_text(statement.raw, 2)) {
            progress.note = reinterpret_cast<const char*>(note);
        }
        progress.updated_at = sqlite3_column_int64(statement.raw, 3);
    }
    return progress;
}

void LearningStore::save_progress(
    const string& function_id,
    int importance,
    int mastery,
    const string& note) {
    Statement statement(
        m_handle.get(),
        "INSERT INTO knowledge_progress(function_id, importance, mastery, note, updated_at) "
        "VALUES(?1, ?2, ?3, ?4, ?5) "
        "ON CONFLICT(function_id) DO UPDATE SET "
        "  importance = excluded.importance,"
        "  mastery = excluded.mastery,"
        "  note = excluded.note,"
        "  updated_at = excluded.updated_at");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    if (sqlite3_bind_int(statement.raw, 2, importance) != SQLITE_OK
        || sqlite3_bind_int(statement.raw, 3, mastery) != SQLITE_OK
        || sqlite3_bind_text(statement.raw, 4, note.c_str(), -1, SQLITE_TRANSIENT) != SQLITE_OK
        || sqlite3_bind_int64(statement.raw, 5, unix_seconds()) != SQLITE_OK) {
        raise_sqlite_error(m_handle.get(), "bind progress parameters");
    }
    if (sqlite3_step(statement.raw) != SQLITE_DONE) {
        raise_sqlite_error(m_handle.get(), "save progress");
    }
}

void LearningStore::record_run(
    const string& function_id,
    const string& output,
    double duration_ms,
    const string& source_hash) {
    Statement statement(
        m_handle.get(),
        "INSERT INTO run_history(function_id, output, duration_ms, source_hash, ran_at) "
        "VALUES(?1, ?2, ?3, ?4, ?5)");
    bind_text(m_handle.get(), statement.raw, 1, function_id);
    bind_text(m_handle.get(), statement.raw, 2, output);
    if (sqlite3_bind_double(statement.raw, 3, duration_ms) != SQLITE_OK
        || sqlite3_bind_text(statement.raw, 4, source_hash.c_str(), -1, SQLITE_TRANSIENT) != SQLITE_OK
        || sqlite3_bind_int64(statement.raw, 5, unix_seconds()) != SQLITE_OK) {
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
        "SELECT id, output, duration_ms, source_hash, ran_at FROM run_history "
        "WHERE function_id = ?1 ORDER BY id DESC LIMIT ?2");
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
        if (const auto* hash = sqlite3_column_text(statement.raw, 3)) {
            record.source_hash = reinterpret_cast<const char*>(hash);
        }
        record.ran_at = sqlite3_column_int64(statement.raw, 4);
        records.push_back(move(record));
    }
    return records;
}
