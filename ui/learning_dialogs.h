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
    // 现场调 AI，请它从整体和局部两个角度讲解这个知识点的真实源码——
    // 整体：这段代码整体在做什么、为什么这样设计、跟这个知识点想教的
    // 概念是什么关系；局部：关键行为、容易忽略的细节、常见误用。不限定
    // 只讲“编译器背后做了什么”，那只是局部视角可能覆盖到的一种情况，
    // 不是全部知识点都用得上。结果按 (function_id, 源码快照) 缓存进
    // LearningStore：源码没变就直接展示上次生成的内容，不用重新等一次
    // AI 请求；源码变了（缓存的 source_snapshot 对不上当前源码）才会
    // 重新生成，覆盖旧缓存。跟“AI 讲解差异”共用同一套 Markdown 对话框
    // 渲染（show_ai_markdown()），不是手册那种静态、需要人工审核的
    // 文档。未配置任何 AI 服务商 Key 时只提示去“设置”里配置，不发起
    // 请求。
    void show_ai_insight(const DialogTopic& topic);

private:
    // 应用内设置（SQLite）优先，读不到再退回同名环境变量。
    string resolve_api_key(
        const string& setting_key,
        const char* env_var_name) const;
    // on_success 在 AI 请求成功（result.ok）之后、结果已经渲染到对话框
    // 里之后调用，参数是最终的 Markdown 正文；请求失败或未配置时不调用
    // ——只有真正拿到的讲解内容才值得写入缓存，请求失败展示的错误提示
    // 不该被当成“讲解结果”存起来。默认空，大多数调用方（AI 自测、AI
    // 讲解差异）不需要缓存结果，只有“AI 讲解”需要。
    void show_ai_markdown(
        const string& dialog_title,
        const string& prompt,
        const string& ark_api_key,
        const string& deepseek_api_key,
        const string& loading_markdown,
        int width,
        int height,
        function<void(const string&)> on_success = nullptr);
    void show_ai_response(
        const string& dialog_title,
        const string& prompt,
        const string& ark_api_key,
        const string& deepseek_api_key);
    // 展示一份已经拿在手里的 Markdown 内容，不发起任何请求——AI 讲解
    // 命中缓存时用这个，跟 show_ai_markdown() 共用同一套排版（md4c 转
    // HTML、WKWebView 渲染），区别只是没有“正在请求”过渡态和后台线程。
    void show_static_markdown(
        const string& dialog_title, const string& markdown, int width, int height);

    Gtk::Window& m_parent;
    const ContentLoader& m_content_loader;
    LearningStore* m_learning_store = nullptr;
    shared_ptr<atomic_bool> m_ui_alive;
};
