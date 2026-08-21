#pragma once

#include <map>
#include <memory>
#include <string>
#include <vector>

using namespace std;

struct sqlite3;

struct RunRecord {
    long long id = 0;
    string output;
    double duration_ms = 0.0;
    string source_snapshot;  // 运行时该知识点成员函数体的完整源码文本
    string git_commit;       // 运行时 HEAD 的短哈希；不在 git 仓库中时为空
    bool git_dirty = false;  // 运行时该源文件相对 git_commit 是否有未提交改动
    long long ran_at = 0;
};

// 基于 SQLite 的本地学习数据存储：AI 自测得出的熟练度、运行历史，以及
// 少量应用设置（目前只有 AI 服务商 API Key）。设置数据跟学习数据在概念
// 上不同源，但数据量很小，复用同一个 SQLite 连接，不为两条 key-value
// 配置另开一个数据库文件。
// 句柄由 RAII 管理；database_path 传 ":memory:" 可用于测试。数据库文件
// （":memory:" 除外）打开后会被设为仅当前用户可读写（0600），降低本机
// 其他账户或备份/同步工具误把明文 Key 带出去的风险——这不是加密，只挡
// 最基础的意外泄露；真正的机密应使用系统钥匙串，这里的取舍见调用方。
// 只在主线程使用；打开或执行失败时抛出 runtime_error。
class LearningStore {
public:
    explicit LearningStore(const string& database_path);
    ~LearningStore();

    LearningStore(const LearningStore&) = delete;
    LearningStore& operator=(const LearningStore&) = delete;

    int load_mastery(const string& function_id) const;
    void save_mastery(const string& function_id, int mastery);
    // 学习进度统计页一次性批量读取全部知识点的熟练度，避免逐个
    // function_id 单独查询；只返回有过记录的条目，未评的知识点不在
    // 返回结果里（调用方按 0 处理）。
    map<string, int> load_all_mastery() const;

    void record_run(
        const string& function_id,
        const string& output,
        double duration_ms,
        const string& source_snapshot,
        const string& git_commit,
        bool git_dirty);
    vector<RunRecord> recent_runs(const string& function_id, int limit) const;

    // 通用的应用设置读写（目前只用来存 AI 服务商 API Key）。key 不存在时
    // get_setting 返回空串，调用方按"未配置"处理，不区分"从未设置"和
    // "显式设为空"。value 传空串等价于清除这条设置（DELETE 而不是留一行
    // 空值），避免空字符串和"未配置"在后续查询里产生歧义。
    string get_setting(const string& key) const;
    void set_setting(const string& key, const string& value);

private:
    struct Sqlite3Deleter {
        void operator()(sqlite3* handle) const noexcept;
    };

    void execute(const string& sql) const;
    // 把旧版本单一 status 位标志列迁移为 mastery 列；CREATE TABLE IF NOT
    // EXISTS 对已存在的旧表是空操作，新列需要显式补齐。旧版本短暂存在过
    // 的 importance/note 列、run_history 的旧 source_hash 列如果已经
    // 存在，留在表里保全旧数据，但运行时不再读写，不做 DROP COLUMN 迁移。
    void migrate_legacy_status_column();
    // run_history 补齐 source_snapshot、git_commit、git_dirty 列（曾用
    // source_hash 只存哈希，无法还原源码；现在改存完整快照，并额外记录
    // 运行时的 git 提交与是否有未提交改动，供历史对比追溯到具体提交）。
    void migrate_legacy_run_history_columns();

    unique_ptr<sqlite3, Sqlite3Deleter> m_handle;
};
