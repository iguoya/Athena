#include "api_key_store.h"

#include <glib.h>

#include <exception>
#include <iostream>

using namespace std;

namespace {

// AI 服务商 Key 在 LearningStore.app_settings 里的存储键；应用内设置面板
// 写入，需要 Key 的地方统一经 ApiKeyStore 读，不再散落地读环境变量。
const char* kSettingArkApiKey = "ai_provider_key_ark";
const char* kSettingDeepseekApiKey = "ai_provider_key_deepseek";

} // namespace

ApiKeyStore::ApiKeyStore(LearningStore* learning_store)
    : m_learning_store(learning_store) {}

string ApiKeyStore::resolve(
    const string& setting_key,
    const char* env_var_name) const {
    if (m_learning_store) {
        try {
            const string stored = m_learning_store->get_setting(setting_key);
            if (!stored.empty()) {
                return stored;
            }
        } catch (const exception& error) {
            cerr << "Failed to read AI key setting " << setting_key << ": "
                 << error.what() << endl;
        }
    }
    const char* env_value = g_getenv(env_var_name);
    return env_value ? env_value : "";
}

string ApiKeyStore::ark_key() const {
    return resolve(kSettingArkApiKey, "ATHENA_ARK_API_KEY");
}

string ApiKeyStore::deepseek_key() const {
    return resolve(kSettingDeepseekApiKey, "ATHENA_DEEPSEEK_API_KEY");
}

bool ApiKeyStore::has_any_key() const {
    return !ark_key().empty() || !deepseek_key().empty();
}

void ApiKeyStore::save(const string& ark_key, const string& deepseek_key) {
    if (!m_learning_store) {
        return;
    }
    try {
        m_learning_store->set_setting(kSettingArkApiKey, ark_key);
        m_learning_store->set_setting(kSettingDeepseekApiKey, deepseek_key);
    } catch (const exception& error) {
        cerr << "Failed to save AI key settings: " << error.what() << endl;
    }
}
