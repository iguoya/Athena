#pragma once

#include "content/content_loader.h"
#include "storage/learning_store.h"
#include "ui/ai_markdown_dialog.h"
#include "ui/api_key_store.h"
#include "ui/dialog_topic.h"

#include <gtkmm.h>

using namespace std;

// “运行历史”对话框：左侧最近运行列表，右侧最多并排对比 2 条记录的源码
// 快照与输出。配置了 AI 服务商 Key 时另有“AI 讲解差异”按钮，把两条记录
// 一并发给 AI 解释改动与结果变化的关系（复用 AiMarkdownDialog）。
class HistoryDialog final {
public:
    HistoryDialog(
        Gtk::Window& parent,
        const ContentLoader& content_loader,
        LearningStore* learning_store,
        ApiKeyStore& api_keys,
        AiMarkdownDialog& ai_markdown);

    void show(const DialogTopic& topic);

private:
    Gtk::Window& m_parent;
    const ContentLoader& m_content_loader;
    LearningStore* m_learning_store = nullptr;
    ApiKeyStore& m_api_keys;
    AiMarkdownDialog& m_ai_markdown;
};
