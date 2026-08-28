#pragma once

#include "storage/learning_store.h"

#include <string>

using namespace std;

// AI 服务商 API Key 的读写：应用内设置（SQLite `app_settings`）优先，
// 读不到再回退到同名环境变量。保存时总是写回应用内设置，不回写环境变量。
// 从 LearningDialogs 提出来，因为设置面板、运行历史、AI 讲解、AI 自测
// 四处都要按同一套顺序取 Key，不该各写一遍、也不该散落地读环境变量。
class ApiKeyStore final {
public:
    // learning_store 允许为 nullptr（数据库打开失败时应用仍可运行）：
    // 此时 Key 只能来自环境变量，save() 静默失败。
    explicit ApiKeyStore(LearningStore* learning_store);

    string ark_key() const;
    string deepseek_key() const;
    // 两个 Key 都为空时返回 false；调用方据此决定是否提示用户去“设置”配置。
    bool has_any_key() const;

    // 把两个 Key 写回应用内设置（空字符串等价于清除）。
    void save(const string& ark_key, const string& deepseek_key);

private:
    string resolve(const string& setting_key, const char* env_var_name) const;

    LearningStore* m_learning_store = nullptr;
};
