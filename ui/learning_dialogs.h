#pragma once

#include "content/content_loader.h"
#include "storage/learning_store.h"
#include "ui/ai_insight_dialog.h"
#include "ui/ai_markdown_dialog.h"
#include "ui/api_key_store.h"
#include "ui/dialog_topic.h"
#include "ui/history_dialog.h"
#include "ui/quiz_dialog.h"
#include "ui/settings_dialog.h"

#include <gtkmm.h>

#include <atomic>
#include <functional>
#include <memory>

using namespace std;

// 学习流程相关对话框的门面：装配共享的 ApiKeyStore 与 AiMarkdownDialog，
// 把四个入口路由到各自独立的对话框模块（设置 / 运行历史 / AI 讲解 /
// AI 自测）。每个子对话框只有单一职责，见各自头文件；本类不含对话框内部
// 逻辑，只负责组合和转发，保持 `CodeChapterPage` 一侧的调用接口稳定。
// 见 ADR 0014、ADR 0016。
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

    void show_settings() { m_settings.show(); }
    void show_history(const DialogTopic& topic) { m_history.show(topic); }
    // on_mastery_changed 在用户答完全部题目后被调用一次，参数是本地公式
    // 换算出的 0-5 星熟练度，返回是否成功持久化。
    void show_quiz(
        const DialogTopic& topic,
        function<bool(int)> on_mastery_changed) {
        m_quiz.show(topic, std::move(on_mastery_changed));
    }
    void show_ai_insight(const DialogTopic& topic) { m_insight.show(topic); }

private:
    // 声明顺序即构造顺序：共享依赖（Key 读写、Markdown 通道）先于用到
    // 它们的子对话框。
    ApiKeyStore m_api_keys;
    AiMarkdownDialog m_ai_markdown;
    SettingsDialog m_settings;
    HistoryDialog m_history;
    QuizDialog m_quiz;
    AiInsightDialog m_insight;
};
