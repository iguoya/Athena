#pragma once

#include <map>
#include <memory>
#include <optional>
#include <string>

using namespace std;

struct sqlite3;

// “AI 讲解”结果缓存：source_snapshot 是生成这份讲解时该知识点成员函数
// 的完整源码文本——调用方用它跟当前源码比对，源码变了就不该继续信任
// 缓存内容，而不是无条件展示一份可能已经过时的讲解。
struct AiInsightRecord {
    string markdown;
    string source_snapshot;
};

// 基于 SQLite 的本地学习数据存储：AI 自测得出的熟练度、AI 讲解缓存，以及
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

    // 最近一次评定的原始成绩：correct / total 为 0 表示还没考过。
    // 光有星级说不清"这 5 星是怎么来的"，界面要能显示依据。
    struct Assessment {
        int mastery = 0;
        int correct = 0;
        int total = 0;
        long long updated_at = 0;
    };
    Assessment load_assessment(const string& function_id) const;
    // 由作答流水派生的量（仓库 ADR 0052：激励与统计是同一条回路）。
    // 先记全，再派生——只存「最新一次成绩」算不出这些。
    struct LearningStats {
        // 今天完成的考核次数
        int attempts_today = 0;
        // 今天答对的题数与总题数
        int correct_today = 0;
        int answered_today = 0;
        // 连续有记录的日历日；今天没记录时算的是截至昨天的
        int streak_days = 0;
        // 累计完成的考核次数
        int attempts_total = 0;
    };

    // 从 assessment_attempt 流水派生统计。没有记录时全为 0。
    LearningStats load_stats() const;

    void save_assessment(
        const string& function_id, int mastery, int correct, int total);
    map<string, Assessment> load_all_assessments() const;
    // 学习进度统计页一次性批量读取全部知识点的熟练度，避免逐个
    // function_id 单独查询；只返回有过记录的条目，未评的知识点不在
    // 返回结果里（调用方按 0 处理）。
    map<string, int> load_all_mastery() const;

    // “AI 讲解”结果缓存，一个知识点只保留最近一次，下次打开同一个
    // 知识点、源码没变的话直接展示缓存，
    // 不用再等一次 AI 请求。没有缓存记录时返回 nullopt。
    optional<AiInsightRecord> load_ai_insight(const string& function_id) const;
    void save_ai_insight(
        const string& function_id,
        const string& source_snapshot,
        const string& markdown);

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
    // 的 importance/note 列如果已经存在，留在表里保全旧数据，但运行时
    // 不再读写，不做 DROP COLUMN 迁移。旧库的 run_history 表也保持原样，
    // 不删除、不迁移、不再追加。
    void migrate_legacy_status_column();
    void migrate_assessment_columns();

    unique_ptr<sqlite3, Sqlite3Deleter> m_handle;
};
