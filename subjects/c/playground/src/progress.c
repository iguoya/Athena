#include "progress.h"

#include <sqlite3.h>
#include <stdio.h>
#include <string.h>

void progress_open(struct Progress* progress, const char* store_path) {
    progress->handle = NULL;
    if (store_path == NULL || store_path[0] == '\0') {
        return;
    }

    sqlite3* handle = NULL;
    // 只读写已有的库，不创建：库和表都由主程序负责建立。
    if (sqlite3_open_v2(store_path, &handle, SQLITE_OPEN_READWRITE, NULL)
        != SQLITE_OK) {
        fprintf(stderr, "学习库不可用（%s），本次不记录进度\n", store_path);
        sqlite3_close(handle);
        return;
    }
    // 两个进程会同时读写同一个文件，WAL 让读写不互相阻塞；写入频率很低
    // （一次自测一行），冲突时靠 busy_timeout 重试即可。
    sqlite3_exec(handle, "PRAGMA journal_mode=WAL", NULL, NULL, NULL);
    sqlite3_busy_timeout(handle, 3000);
    progress->handle = handle;
}

void progress_close(struct Progress* progress) {
    if (progress->handle != NULL) {
        sqlite3_close((sqlite3*)progress->handle);
        progress->handle = NULL;
    }
}

int progress_load_mastery(
    const struct Progress* progress, const char* topic_id) {
    if (progress->handle == NULL) {
        return 0;
    }
    sqlite3_stmt* statement = NULL;
    const char* sql =
        "SELECT mastery FROM knowledge_progress WHERE function_id = ?";
    if (sqlite3_prepare_v2((sqlite3*)progress->handle, sql, -1, &statement, NULL)
        != SQLITE_OK) {
        return 0;
    }
    sqlite3_bind_text(statement, 1, topic_id, -1, SQLITE_STATIC);
    int mastery = 0;
    if (sqlite3_step(statement) == SQLITE_ROW) {
        mastery = sqlite3_column_int(statement, 0);
    }
    sqlite3_finalize(statement);
    return mastery;
}

int progress_save_mastery(
    const struct Progress* progress, const char* topic_id, int mastery) {
    if (progress->handle == NULL) {
        return 0;
    }
    sqlite3_stmt* statement = NULL;
    const char* sql =
        "INSERT INTO knowledge_progress (function_id, mastery) VALUES (?, ?) "
        "ON CONFLICT(function_id) DO UPDATE SET mastery = excluded.mastery";
    if (sqlite3_prepare_v2((sqlite3*)progress->handle, sql, -1, &statement, NULL)
        != SQLITE_OK) {
        return 0;
    }
    sqlite3_bind_text(statement, 1, topic_id, -1, SQLITE_STATIC);
    sqlite3_bind_int(statement, 2, mastery);
    const int done = sqlite3_step(statement) == SQLITE_DONE;
    sqlite3_finalize(statement);
    return done;
}
