#include "ai_insight_dialog.h"

#include "content/source_locator.h"
#include "ui/ai_prompt_style.h"

#include <exception>
#include <iostream>
#include <string>

using namespace std;

AiInsightDialog::AiInsightDialog(
    Gtk::Window& parent,
    const ContentLoader& content_loader,
    LearningStore* learning_store,
    ApiKeyStore& api_keys,
    AiMarkdownDialog& ai_markdown)
    : m_parent(parent),
      m_content_loader(content_loader),
      m_learning_store(learning_store),
      m_api_keys(api_keys),
      m_ai_markdown(ai_markdown) {}

// 缓存命中判断放在“检查 Key”之前：哪怕当前没配置任何服务商 Key，只要
// 之前生成过、源码没变，也应该能看到上次的讲解结果，不用被“未配置”
// 提示挡住——缓存内容不依赖当前是否还能发起新请求。
void AiInsightDialog::show(const DialogTopic& topic) {
    const string source = load_member_source_text(
                              m_content_loader, topic.source_path,
                              topic.member_name)
                              .value_or("");

    if (m_learning_store) {
        try {
            if (const auto cached =
                    m_learning_store->load_ai_insight(topic.function_id);
                cached && !source.empty() && cached->source_snapshot == source) {
                m_ai_markdown.show_static(
                    "AI 讲解：" + topic.title, cached->markdown, 1040, 780);
                return;
            }
        } catch (const exception& error) {
            cerr << "Failed to load cached AI insight for " << topic.function_id
                 << ": " << error.what() << endl;
        }
    }

    if (!m_api_keys.has_any_key()) {
        auto notice = Gtk::make_managed<Gtk::MessageDialog>(
            m_parent,
            "AI 讲解需要先在侧边栏底部“设置”里配置至少一个 AI 服务商 Key",
            false,
            Gtk::MessageType::INFO,
            Gtk::ButtonsType::OK,
            true);
        notice->signal_response().connect([notice](int) { notice->hide(); });
        notice->show();
        return;
    }

    const string prompt =
        "请从整体和局部两个角度讲解 C++ 知识点「" + topic.title + "」下面这段"
        "真实源码。整体角度：这段代码整体在做什么、为什么这样设计、跟这个"
        "知识点想教的概念是什么关系、在什么场景下会用到。局部角度：关键"
        "实现细节、容易被忽略或误解的地方、常见误用；如果这段代码里确实"
        "存在源码字面看不出来、但运行时真实发生的行为（比如隐式转换、临时"
        "对象产生和销毁时机、RAII 对象析构时点、编译器可能做的优化或省略），"
        "也在局部角度里讲，但不要把整篇讲解都局限在这一类细节上，更不要"
        "为了凑内容而讲跟这段代码无关的语言特性列表。" +
        string(kChineseTutorialStyleHint) + "\n\n=== 知识点说明 ===\n" +
        topic.description + "\n\n=== 源码 ===\n" + source;

    auto store = m_learning_store;
    const string function_id = topic.function_id;
    m_ai_markdown.show_request(
        "AI 讲解：" + topic.title,
        prompt,
        {.ark = m_api_keys.ark_key(), .deepseek = m_api_keys.deepseek_key()},
        "正在请求 AI，请稍候…",
        1040,
        780,
        [store, function_id, source](const string& markdown) {
            if (!store) {
                return;
            }
            try {
                store->save_ai_insight(function_id, source, markdown);
            } catch (const exception& error) {
                cerr << "Failed to cache AI insight for " << function_id << ": "
                     << error.what() << endl;
            }
        });
}
