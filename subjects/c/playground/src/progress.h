#ifndef ATHENA_C_PROGRESS_H
#define ATHENA_C_PROGRESS_H

// 与主程序共用同一个 SQLite 学习库（ADR 0032）。数据库路径由启动方通过
// --store 传入，本程序不自己推导用户数据目录——那样两边就得各写一套平台
// 规则，是没必要的重复。
//
// 表结构的 owner 是主程序：这里只读写约定好的 knowledge_progress 两列，
// 不建表、不迁移、不改结构。知识点 ID 一律以 "c." 开头，与主程序的
// "cpp." / "practice." 天然不冲突。

struct Progress {
    void* handle; // sqlite3*，为空表示没有可用的学习库
};

// 打开学习库。store_path 为 NULL、文件打不开或表不存在时不算错误：
// progress.handle 置空，其余功能照常工作，只是不记进度。
void progress_open(struct Progress* progress, const char* store_path);
void progress_close(struct Progress* progress);

// 读取熟练度（0-5）。没有记录或没有学习库时返回 0。
int progress_load_mastery(const struct Progress* progress, const char* topic_id);

// 写入熟练度。没有学习库时静默跳过；返回是否写入成功。
int progress_save_mastery(
    const struct Progress* progress, const char* topic_id, int mastery);

#endif
