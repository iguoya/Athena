#pragma once

#include "content/content_loader.h"
#include "ui/api_key_store.h"
#include "ui/dialog_topic.h"

#include <gtkmm.h>

#include <atomic>
#include <functional>
#include <memory>

using namespace std;

// “AI 自测”对话框：请 AI 以 JSON 返回针对该知识点具体源码的选择题，用
// GTK 控件（不是 Markdown/WebView）逐题渲染，本地判分。用户答完全部有效
// 题目后按固定公式换算 0-5 星熟练度，通过调用方传入的回调回写。
class QuizDialog final {
public:
    // ui_alive 由窗口持有并在析构时置 false，供异步回传的回调判断控件
    // 是否仍然可用。
    QuizDialog(
        Gtk::Window& parent,
        const ContentLoader& content_loader,
        ApiKeyStore& api_keys,
        shared_ptr<atomic_bool> ui_alive);

    // on_mastery_changed 在用户答完全部题目后被调用一次，参数是本地公式
    // 换算出的 0-5 星熟练度，返回是否成功持久化。
    void show(
        const DialogTopic& topic,
        function<bool(int)> on_mastery_changed);

private:
    Gtk::Window& m_parent;
    const ContentLoader& m_content_loader;
    ApiKeyStore& m_api_keys;
    shared_ptr<atomic_bool> m_ui_alive;
};
