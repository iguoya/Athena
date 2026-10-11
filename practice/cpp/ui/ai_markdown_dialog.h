#pragma once

#include "content/content_loader.h"

#include <gtkmm.h>

#include <atomic>
#include <functional>
#include <memory>
#include <string>

using namespace std;

// AI 回答的 Markdown 展示通道：先解析为 DocModel，再由跨平台 GTK 控件
// 呈现，和手册及学习工作台共享标题、代码块、列表等排版能力。AI 讲解和
// AI 自测共用它；网络请求在独立线程执行，控件只在主线程更新。从
// LearningDialogs 提出来，是纯粹的“把一段 Markdown（现成的或异步取回的）
// 显示出来”的能力，不含任何提示词或业务判断。
class AiMarkdownDialog final {
public:
    // ui_alive 由窗口持有并在析构时置 false，供异步回传的 idle 回调判断
    // 控件是否仍然可用。
    AiMarkdownDialog(
        Gtk::Window& parent,
        const ContentLoader& content_loader,
        shared_ptr<atomic_bool> ui_alive);

    struct ApiKeys {
        string ark;
        string deepseek;
    };

    // 打开对话框，先显示 loading_markdown，异步用 prompt 调 AI（优先豆包，
    // 失败或未配置退回 DeepSeek），结果到达后替换为最终内容。on_success 只
    // 在请求成功（result.ok）且结果已渲染后调用，参数是最终 Markdown 正文；
    // 请求失败展示的是错误提示，不触发回调——只有真正拿到的内容才值得被
    // 调用方（如 AI 讲解的缓存写入）存起来。
    void show_request(
        const string& dialog_title,
        const string& prompt,
        const ApiKeys& keys,
        const string& loading_markdown,
        int width,
        int height,
        function<void(const string&)> on_success = nullptr);

    // 展示一份已经拿在手里的 Markdown，不发起请求、不起后台线程，打开即
    // 所见——AI 讲解命中缓存时用这个。
    void show_static(
        const string& dialog_title,
        const string& markdown,
        int width,
        int height);

private:
    Gtk::Window& m_parent;
    const ContentLoader& m_content_loader;
    shared_ptr<atomic_bool> m_ui_alive;
};
