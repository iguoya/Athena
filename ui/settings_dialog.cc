#include "settings_dialog.h"

#include "ui/dialog_helpers.h"

#include <string>

using namespace std;

SettingsDialog::SettingsDialog(Gtk::Window& parent, ApiKeyStore& api_keys)
    : m_parent(parent), m_api_keys(api_keys) {}

// 两个 AI 服务商 Key 用 Gtk::PasswordEntry（自带显示/隐藏切换）承载，
// 预填当前值（应用内设置优先，读不到再显示环境变量里的值——纯展示用，
// 保存时总是写回应用内设置，不回写环境变量，环境变量本来就不该被程序改）。
// 保存后旧对话框实例拿到过时 Key 快照的问题不存在——每次要用 Key 都会
// 重新经 ApiKeyStore 读，不缓存。
void SettingsDialog::show() {
    auto dialog = new Gtk::Dialog();
    dialog->set_title("设置");
    dialog->set_default_size(480, 220);

    auto* content = dialog->get_content_area();
    auto page = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 14);
    page->set_margin_top(20);
    page->set_margin_bottom(20);
    page->set_margin_start(24);
    page->set_margin_end(24);
    content->append(*page);

    auto heading = Gtk::make_managed<Gtk::Label>("AI 服务商 API Key");
    heading->add_css_class("title-4");
    heading->set_halign(Gtk::Align::START);
    page->append(*heading);

    auto hint = Gtk::make_managed<Gtk::Label>(
        "用于“AI 自测”“AI 讲解差异”。保存在本机应用数据目录的 SQLite "
        "文件里（仅当前用户可读写），不上传、不同步。留空等价于未配置。");
    hint->add_css_class("dim-label");
    hint->set_wrap(true);
    hint->set_halign(Gtk::Align::START);
    page->append(*hint);

    const auto add_key_row =
        [page](const string& label_text, const string& initial_value) {
            auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
            auto label = Gtk::make_managed<Gtk::Label>(label_text);
            label->set_halign(Gtk::Align::START);
            row->append(*label);
            auto entry = Gtk::make_managed<Gtk::PasswordEntry>();
            entry->set_show_peek_icon(true);
            entry->set_text(initial_value);
            row->append(*entry);
            page->append(*row);
            return entry;
        };

    auto* ark_entry = add_key_row(
        "火山方舟豆包（ATHENA_ARK_API_KEY）", m_api_keys.ark_key());
    auto* deepseek_entry = add_key_row(
        "DeepSeek（ATHENA_DEEPSEEK_API_KEY）", m_api_keys.deepseek_key());

    auto save_button = Gtk::make_managed<Gtk::Button>("保存");
    save_button->add_css_class("btn-primary");
    save_button->signal_clicked().connect(
        [this, dialog, ark_entry, deepseek_entry]() {
            m_api_keys.save(
                string(ark_entry->get_text()),
                string(deepseek_entry->get_text()));
            dialog->close();
        });
    append_dialog_action_bar(content, {save_button});

    lock_for_modal_dialog(m_parent, *dialog);
}
