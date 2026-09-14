#pragma once

#include "content/content_loader.h"
#include "storage/learning_store.h"
#include "ui/ai_markdown_dialog.h"
#include "ui/api_key_store.h"
#include "ui/dialog_topic.h"

#include <gtkmm.h>

using namespace std;

// “AI 讲解”：现场把知识点真实源码发给 AI，请它从整体和局部两个角度讲解。
// 结果按 (function_id, 源码快照) 缓存进 LearningStore：源码没变直接展示
// 缓存，源码变了或从没生成过才真正请求。跟手册“说明文档”（本地静态、需
// 人工审核、不联网）互补。
class AiInsightDialog final {
public:
    AiInsightDialog(
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
