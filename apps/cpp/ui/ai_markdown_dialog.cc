#include "ai_markdown_dialog.h"

#include "render/document_view.h"
#include "services/ai_service.h"
#include "ui/dialog_helpers.h"

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
    auto document_view = make_shared<DocumentView>();
    content->append(document_view->widget());

    auto dialog_alive = make_shared<atomic_bool>(true);
    dialog->signal_hide().connect([dialog_alive]() {
        dialog_alive->store(false);
    });
    lock_for_modal_dialog(m_parent, *dialog);
    document_view->set_markdown(loading_markdown);

    auto alive = m_ui_alive;
    thread([alive, dialog_alive, document_view, keys,
            prompt, dialog, on_success]() {
        const AiChatResult result = AiService().chat(
            {.ark_api_key = keys.ark, .deepseek_api_key = keys.deepseek},
            prompt);
        Glib::signal_idle().connect_once(
            [alive, dialog_alive, document_view,
             result, dialog, on_success]() {
                if (!alive->load() || !dialog_alive->load()) {
                    return;
                }
                const string markdown =
                    result.ok ? result.content : ("# 请求失败\n\n" + result.error);
                document_view->set_markdown(markdown);
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
    auto document_view = make_shared<DocumentView>();
    content->append(document_view->widget());
    lock_for_modal_dialog(m_parent, *dialog);
    document_view->set_markdown(markdown);
}
