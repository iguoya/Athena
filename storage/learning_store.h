#pragma once

#include <memory>
#include <string>
#include <vector>

using namespace std;

struct sqlite3;

struct KnowledgeProgress {
    int mastery = 0;  // 0-5 星：熟练度，用户自由评分，0 = 未处理，5 = 完全掌握
    string note;
    long long updated_at = 0;
};

struct RunRecord {
    long long id = 0;
    string output;
    double duration_ms = 0.0;
    string source_snapshot;  // 运行时该知识点成员函数体的完整源码文本
    string git_commit;       // 运行时 HEAD 的短哈希；不在 git 仓库中时为空
    bool git_dirty = false;  // 运行时该源文件相对 git_commit 是否有未提交改动
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
        int mastery,
        const string& note);

    void record_run(
        const string& function_id,
        const string& output,
        double duration_ms,
        const string& source_snapshot,
        const string& git_commit,
        bool git_dirty);
    vector<RunRecord> recent_runs(const string& function_id, int limit) const;

private:
    struct Sqlite3Deleter {
        void operator()(sqlite3* handle) const noexcept;
    };

    void execute(const string& sql) const;
    // 把旧版本单一 status 位标志列迁移为 mastery 列；CREATE TABLE IF NOT
    // EXISTS 对已存在的旧表是空操作，新列需要显式补齐。旧版本短暂存在过
    // 的 importance 列、run_history 的旧 source_hash 列（本会话内引入又
    // 废弃）如果已经加过，留在表里不再使用，不做 DROP COLUMN 迁移。
    void migrate_legacy_status_column();
    // run_history 补齐 source_snapshot、git_commit、git_dirty 列（曾用
    // source_hash 只存哈希，无法还原源码；现在改存完整快照，并额外记录
    // 运行时的 git 提交与是否有未提交改动，供历史对比追溯到具体提交）。
    void migrate_legacy_run_history_columns();

    unique_ptr<sqlite3, Sqlite3Deleter> m_handle;
};
