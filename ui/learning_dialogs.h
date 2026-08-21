#pragma once

#include "content/content_loader.h"
#include "storage/learning_store.h"

#include <gtkmm.h>

#include <atomic>
#include <functional>
#include <memory>
#include <string>

using namespace std;

// 对话框需要的知识点上下文，由代码页在点击“运行历史”“AI 自测”时按当前
// 行填好。`description` 只有 AI 自测用得到（作为出题依据），运行历史不
// 读取它。
struct DialogTopic {
    string function_id;
    string title;
    string description;
    string source_path;
    string member_name;
};

// 设置、运行历史和 AI 自测三类叶子对话框（AI 讲解差异是运行历史的内部
// 动作，不单独对外暴露）。模块只依赖 ContentLoader、LearningStore 和非
// GTK 的 AiService，不反向调用 MainWindow：需要把结果写回主界面时（例如
// 自测评分更新熟练度星级和学习进度页）由调用方传入回调。见 ADR 0014。
class LearningDialogs final {
public:
    // learning_store 允许为 nullptr（数据库打开失败时应用仍可运行）：
    // 设置无法保存、运行历史直接不弹出。ui_alive 由窗口持有并在析构时
    // 置 false，供异步回传的回调判断控件是否仍然可用。
    LearningDialogs(
        Gtk::Window& parent,
        const ContentLoader& content_loader,
        LearningStore* learning_store,
        shared_ptr<atomic_bool> ui_alive);

    void show_settings();
    void show_history(const DialogTopic& topic);
    // on_mastery_changed 在用户答完全部题目后被调用一次，参数是本地公式
    // 换算出的 0-5 星熟练度，返回是否成功持久化。未配置任何 AI 服务商
    // Key 时只提示去“设置”里配置，不发起请求。
    void show_quiz(
        const DialogTopic& topic,
        function<bool(int)> on_mastery_changed);

private:
    // 应用内设置（SQLite）优先，读不到再退回同名环境变量。
    string resolve_api_key(
        const string& setting_key,
        const char* env_var_name) const;
    void show_ai_markdown(
        const string& dialog_title,
        const string& prompt,
        const string& ark_api_key,
        const string& deepseek_api_key,
        const string& loading_markdown,
        int width,
        int height);
    void show_ai_response(
        const string& dialog_title,
        const string& prompt,
        const string& ark_api_key,
        const string& deepseek_api_key);

    Gtk::Window& m_parent;
    const ContentLoader& m_content_loader;
    LearningStore* m_learning_store = nullptr;
    shared_ptr<atomic_bool> m_ui_alive;
};
