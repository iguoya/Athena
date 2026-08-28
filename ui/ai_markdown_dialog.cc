#include "ai_markdown_dialog.h"

#include "render/article_view.h"
#include "render/markdown_renderer.h"
#include "services/ai_service.h"
#include "ui/dialog_helpers.h"
#include "ui/markdown_fallback.h"

#include <thread>
#include <utility>

using namespace std;

AiMarkdownDialog::AiMarkdownDialog(
    Gtk::Window& parent,
    const ContentLoader& content_loader,
    shared_ptr<atomic_bool> ui_alive)
    : m_parent(parent),
      m_content_loader(content_loader),
      m_ui_alive(std::move(ui_alive)) {}

void AiMarkdownDialog::show_request(
    const string& dialog_title,
    const string& prompt,
    const ApiKeys& keys,
    const string& loading_markdown,
    int width,
    int height,
    function<void(const string&)> on_success) {
    auto dialog = new Gtk::Dialog();
    dialog->set_title(dialog_title);
    dialog->set_default_size(width, height);

    auto* content = dialog->get_content_area();
    auto article_host = Gtk::make_managed<Gtk::DrawingArea>();
    article_host->set_hexpand(true);
    article_host->set_vexpand(true);
    content->append(*article_host);

    auto dialog_alive = make_shared<atomic_bool>(true);
    auto article_view = make_shared<unique_ptr<ArticleView>>();
    dialog->signal_hide().connect([dialog_alive, article_view]() {
        dialog_alive->store(false);
        article_view->reset();
    });
    lock_for_modal_dialog(m_parent, *dialog);

    // 只在这几个 AI 对话框里把正文字号调得比手册基准更大一点，保持
    // “对话框内容更醒目”这层相对关系；不改 resources/article.css 本身
    // 的默认值（21px），改了这里也要跟着变，不然手册字号涨了、对话框
    // 反而失去原有的字号优势。
    string stylesheet = m_content_loader.load_resource("/app/article.css");
    if (!stylesheet.empty()) {
        stylesheet += "\n:root { --article-font-size: 24px; }\n";
    }
    *article_view = create_platform_article_view(*article_host, *dialog);

    // 没有 WebView 后端的平台退回纯文本控件显示 Markdown 原文；请求返回后
    // 由 idle 回调把 loading 文本替换成结果。
    auto fallback_text = make_shared<Gtk::TextView*>(nullptr);
    if (!*article_view) {
        article_host->set_visible(false);
        content->append(
            *make_markdown_fallback_view(loading_markdown, fallback_text.get()));
    } else if (!stylesheet.empty()) {
        (*article_view)->load_html(
            render_markdown_html(
                loading_markdown,
                stylesheet,
                parse_markdown_headings(loading_markdown)),
            ATHENA_SOURCE_ROOT);
    }

    auto alive = m_ui_alive;
    thread([alive, dialog_alive, article_view, fallback_text, stylesheet, keys,
            prompt, dialog, on_success]() {
        const AiChatResult result = AiService().chat(
            {.ark_api_key = keys.ark, .deepseek_api_key = keys.deepseek},
            prompt);
        Glib::signal_idle().connect_once(
            [alive, dialog_alive, article_view, fallback_text, stylesheet,
             result, dialog, on_success]() {
                if (!alive->load() || !dialog_alive->load()) {
                    return;
                }
                const string markdown =
                    result.ok ? result.content : ("# 请求失败\n\n" + result.error);
                if (*article_view && !stylesheet.empty()) {
                    (*article_view)->load_html(
                        render_markdown_html(
                            markdown, stylesheet,
                            parse_markdown_headings(markdown)),
                        ATHENA_SOURCE_ROOT);
                } else if (*fallback_text) {
                    (*fallback_text)->get_buffer()->set_text(markdown);
                }
                // 网络请求期间用户可能点过主窗口；结果到达时重新前置一次，
                // 不指望等待开始时的那次 present() 全程保持有效。
                dialog->present();
                // 只有真正请求成功才回调——失败时 markdown 是错误提示，
                // 不是讲解内容，不该被调用方（比如 AI 讲解的缓存写入）
                // 当成结果存起来。
                if (result.ok && on_success) {
                    on_success(result.content);
                }
            });
    }).detach();
}

void AiMarkdownDialog::show_static(
    const string& dialog_title,
    const string& markdown,
    int width,
    int height) {
    auto dialog = new Gtk::Dialog();
    dialog->set_title(dialog_title);
    dialog->set_default_size(width, height);

    auto* content = dialog->get_content_area();
    auto article_host = Gtk::make_managed<Gtk::DrawingArea>();
    article_host->set_hexpand(true);
    article_host->set_vexpand(true);
    content->append(*article_host);

    auto article_view = make_shared<unique_ptr<ArticleView>>();
    dialog->signal_hide().connect([article_view]() { article_view->reset(); });
    lock_for_modal_dialog(m_parent, *dialog);

    string stylesheet = m_content_loader.load_resource("/app/article.css");
    if (!stylesheet.empty()) {
        stylesheet += "\n:root { --article-font-size: 24px; }\n";
    }
    *article_view = create_platform_article_view(*article_host, *dialog);
    if (!*article_view) {
        // 没有 WebView 后端的平台退回纯文本显示 Markdown 原文。
        article_host->set_visible(false);
        content->append(*make_markdown_fallback_view(markdown));
        return;
    }
    if (!stylesheet.empty()) {
        (*article_view)->load_html(
            render_markdown_html(
                markdown, stylesheet, parse_markdown_headings(markdown)),
            ATHENA_SOURCE_ROOT);
    }
}
