#pragma once

#include <memory>
#include <string>
#include <vector>

using namespace std;

struct sqlite3;

struct KnowledgeProgress {
    int importance = 0;  // 0-5 星：重要程度/难度，用户自由评分，0 = 未判断
    int mastery = 0;     // 0-5 星：掌握程度，用户自由评分，0 = 未处理，5 = 完全掌握
    string note;
    long long updated_at = 0;
};

struct RunRecord {
    long long id = 0;
    string output;
    double duration_ms = 0.0;
    string source_hash;
    long long ran_at = 0;
};

// 基于 SQLite 的本地学习数据存储：掌握状态、知识点笔记和运行历史。
// 句柄由 RAII 管理；database_path 传 ":memory:" 可用于测试。
// 只在主线程使用；打开或执行失败时抛出 runtime_error。
class LearningStore {
public:
    explicit LearningStore(const string& database_path);
    ~LearningStore();

    LearningStore(const LearningStore&) = delete;
    LearningStore& operator=(const LearningStore&) = delete;

    KnowledgeProgress load_progress(const string& function_id) const;
    void save_progress(
        const string& function_id,
        int importance,
        int mastery,
        const string& note);

    void record_run(
        const string& function_id,
        const string& output,
        double duration_ms,
        const string& source_hash);
    vector<RunRecord> recent_runs(const string& function_id, int limit) const;

private:
    struct Sqlite3Deleter {
        void operator()(sqlite3* handle) const noexcept;
    };

    void execute(const string& sql) const;
    // 把旧版本单一 status 位标志列迁移为 importance/mastery 两列；
    // CREATE TABLE IF NOT EXISTS 对已存在的旧表是空操作，新列需要显式补齐。
    void migrate_legacy_status_column();

    unique_ptr<sqlite3, Sqlite3Deleter> m_handle;
};
