#include "learning_dialogs.h"

#include "content/source_locator.h"
#include "render/article_view.h"
#include "render/markdown_renderer.h"
#include "services/ai_service.h"

#include <gtksourceview/gtksource.h>

#include <algorithm>
#include <ctime>
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <thread>
#include <vector>

using namespace std;

namespace {

// AI 服务商 Key 在 LearningStore.app_settings 里的存储键；应用内设置面板
// 写入，需要 Key 的地方统一经 resolve_api_key() 读，不再散落地读环境变量。
const char* kSettingArkApiKey = "ai_provider_key_ark";
const char* kSettingDeepseekApiKey = "ai_provider_key_deepseek";

// 讲解类提示词（自测、讲解差异）共用的风格提示：贴近主流中文 C++ 教程的
// 讲法和术语习惯，不生造术语。这里不是真的联网抓取这些站点内容——
// AiService 没有搜索/浏览能力，只是提示模型往这个方向组织语言，权当术语
// 和讲法的锚点。
const char* kChineseTutorialStyleHint =
    "讲解风格和术语尽量贴近菜鸟教程、C语言中文网、微软 Learn 中文文档、"
    "w3cschool 这类主流中文 C++ 教程的习惯讲法，不要生造术语。";

string format_duration_ms(double milliseconds) {
    ostringstream stream;
    if (milliseconds >= 1000.0) {
        stream << fixed << setprecision(2) << milliseconds / 1000.0 << "s";
    } else {
        stream << fixed << setprecision(2) << milliseconds << "ms";
    }
    return stream.str();
}

string format_timestamp(long long seconds) {
    const auto raw = static_cast<time_t>(seconds);
    tm local {};
    localtime_r(&raw, &local);
    ostringstream stream;
    stream << put_time(&local, "%m-%d %H:%M:%S");
    return stream.str();
}

// 在对话框内容区底部居中放一行按钮；不加“关闭”——系统对话框本身自带
// 原生标题栏关闭按钮，不需要重复一个。extra_buttons 为空时什么都不做，
// 调用方自己决定按钮颜色（加 css class）和点击行为。
void append_dialog_action_bar(
    Gtk::Box* content_box,
    const vector<Gtk::Button*>& extra_buttons) {
    if (extra_buttons.empty()) {
        return;
    }
    auto action_bar = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 8);
    action_bar->set_halign(Gtk::Align::CENTER);
    action_bar->add_css_class("dialog-action-bar");

    for (auto* button : extra_buttons) {
        action_bar->append(*button);
    }

    content_box->append(*action_bar);
}

// 打开模态对话框前调用。传入的 dialog 必须是 `new` 出来的普通指针，
// 不能用 Gtk::make_managed 创建——GTK4 里 GtkWindow 的 hide-on-close
// 默认是 false，点原生标题栏关闭按钮会直接销毁窗口而不是隐藏它；如果
// 对话框是 make_managed 出来的，gtkmm 会在底层对象销毁的同时同步
// delete 这份 C++ 包装。AI 讲解/自测这几个对话框还有一个在等待期间
// 继续持有对话框指针、异步网络结果回来后要回填内容并重新前置的后台
// 线程回调——用户在响应还没返回时就把对话框关掉，回调触发时会踩中
// 已经被 delete 掉的悬空指针，是真实的 use-after-free，不是理论风险。
//
// 这里反过来强制 set_hide_on_close(true)：点关闭按钮总是隐藏、不销毁；
// 对话框改由这里在隐藏之后显式 delete——排到事件循环下一轮再删，不在
// hide 信号处理函数内部直接删自己（那个调用栈本身还压在这个对象上，
// 是未定义行为）；调用方自己的 signal_hide 清理逻辑（如翻转
// dialog_alive、reset article_view）要在 lock_for_modal_dialog 之前
// 连接，才能保证在这里删除之前先跑到——GTK 信号按连接顺序调用。
//
// 同时禁用主窗口自身的输入，隐藏时恢复：观察到过等待期间（网络请求慢
// 的话有好几秒到十几秒窗口期）用户点回主窗口、主窗口被系统前置盖住
// 对话框的情况——GTK4 的 set_modal(true) 在这里没能防住。禁用主窗口
// 输入是应用层能做的、不依赖窗口管理器行为的兜底：即便主窗口的原生
// 窗口被前置到对话框之上，用户也点不动里面任何控件。present() 保证
// 首次显示就被前置和聚焦，而不只是 show()。
void lock_for_modal_dialog(Gtk::Window& main_window, Gtk::Dialog& dialog) {
    dialog.set_transient_for(main_window);
    dialog.set_modal(true);
    dialog.set_hide_on_close(true);
    main_window.set_sensitive(false);
    dialog.signal_hide().connect([&main_window, &dialog]() {
        main_window.set_sensitive(true);
        Glib::signal_idle().connect_once([&dialog]() { delete &dialog; });
    });
    dialog.present();
}

// 为只读 GtkSourceView 配置 C++ 语法高亮并填入整段文本；不做成员函数
// 定位/高亮，因为运行历史里的快照本来就已经是单个成员函数体的全文。
void configure_snapshot_source_view(GtkSourceView* source_view, const string& text) {
    if (!source_view) {
        return;
    }
    auto source_buffer = GTK_SOURCE_BUFFER(
        gtk_text_view_get_buffer(GTK_TEXT_VIEW(source_view)));
    auto language_manager = gtk_source_language_manager_get_default();
    auto cpp_language = gtk_source_language_manager_get_language(
        language_manager,
        "cpp");
    if (cpp_language) {
        gtk_source_buffer_set_language(source_buffer, cpp_language);
    }
    gtk_source_buffer_set_highlight_syntax(source_buffer, true);
    gtk_source_buffer_set_highlight_matching_brackets(source_buffer, true);

    auto scheme_manager = gtk_source_style_scheme_manager_get_default();
    auto scheme = gtk_source_style_scheme_manager_get_scheme(
        scheme_manager,
        "Adwaita");
    if (scheme) {
        gtk_source_buffer_set_style_scheme(source_buffer, scheme);
    }

    const string display_text =
        text.empty() ? "（该次运行未保存源码快照）" : text;
    gtk_text_buffer_set_text(
        GTK_TEXT_BUFFER(source_buffer),
        display_text.c_str(),
        static_cast<int>(display_text.size()));
}

// 历史记录行末尾的简短 git 标记，如 "a1b2c3d"（有未提交改动则加 "+"）；
// 不在 git 仓库中运行时返回空串，调用方按需拼接。
string format_git_tag(const RunRecord& run) {
    if (run.git_commit.empty()) {
        return "";
    }
    return run.git_commit + (run.git_dirty ? "+" : "");
}

// 对比栏标题用的完整 git 版本描述，可配合 `git show <commit>` 之类命令
// 在仓库里追溯该次运行时的完整提交上下文。
string format_git_summary(const RunRecord& run) {
    if (run.git_commit.empty()) {
        return "未在 git 仓库中运行";
    }
    return "commit " + run.git_commit
        + (run.git_dirty ? "（工作区有未提交改动）" : "");
}

} // namespace

LearningDialogs::LearningDialogs(
    Gtk::Window& parent,
    const ContentLoader& content_loader,
    LearningStore* learning_store,
    shared_ptr<atomic_bool> ui_alive)
    : m_parent(parent),
      m_content_loader(content_loader),
      m_learning_store(learning_store),
      m_ui_alive(std::move(ui_alive)) {}

string LearningDialogs::resolve_api_key(
    const string& setting_key,
    const char* env_var_name) const {
    if (m_learning_store) {
        try {
            const string stored = m_learning_store->get_setting(setting_key);
            if (!stored.empty()) {
                return stored;
            }
        } catch (const exception& error) {
            cerr << "Failed to read AI key setting " << setting_key << ": "
                 << error.what() << endl;
        }
    }
    const char* env_value = g_getenv(env_var_name);
    return env_value ? env_value : "";
}

// 设置面板：目前只有两个 AI 服务商 Key，用 Gtk::PasswordEntry（自带
// 显示/隐藏切换）承载，预填当前值（应用内设置优先，读不到再显示环境
// 变量里的值——纯展示用，保存时总是写回应用内设置，不回写环境变量，
// 环境变量本来就不该被程序改）。保存后旧的对话框实例已经拿到过时 Key
// 快照的问题不存在——每次点“运行历史”“AI 自测”都会重新调用
// resolve_api_key()，不缓存。
void LearningDialogs::show_settings() {
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
        "火山方舟豆包（ATHENA_ARK_API_KEY）",
        resolve_api_key(kSettingArkApiKey, "ATHENA_ARK_API_KEY"));
    auto* deepseek_entry = add_key_row(
        "DeepSeek（ATHENA_DEEPSEEK_API_KEY）",
        resolve_api_key(kSettingDeepseekApiKey, "ATHENA_DEEPSEEK_API_KEY"));

    auto save_button = Gtk::make_managed<Gtk::Button>("保存");
    save_button->add_css_class("btn-primary");
    save_button->signal_clicked().connect(
        [this, dialog, ark_entry, deepseek_entry]() {
            if (m_learning_store) {
                try {
                    m_learning_store->set_setting(
                        kSettingArkApiKey, string(ark_entry->get_text()));
                    m_learning_store->set_setting(
                        kSettingDeepseekApiKey,
                        string(deepseek_entry->get_text()));
                } catch (const exception& error) {
                    cerr << "Failed to save AI key settings: " << error.what()
                         << endl;
                }
            }
            dialog->close();
        });
    append_dialog_action_bar(content, {save_button});

    lock_for_modal_dialog(m_parent, *dialog);
}

void LearningDialogs::show_history(const DialogTopic& topic) {
    if (!m_learning_store) {
        return;
    }
    const string topic_title = topic.title;
    vector<RunRecord> runs;
    try {
        runs = m_learning_store->recent_runs(topic.function_id, 20);
    } catch (const exception& error) {
        cerr << "Failed to load run history for " << topic.function_id << ": "
             << error.what() << endl;
    }
    const string current_snapshot = load_member_source_text(
                                        m_content_loader,
                                        topic.source_path,
                                        topic.member_name)
                                        .value_or("");

    auto dialog = new Gtk::Dialog();
    dialog->set_title("运行历史：" + topic_title);
    dialog->set_default_size(1100, 680);

    auto* content = dialog->get_content_area();
    auto paned = Gtk::make_managed<Gtk::Paned>(Gtk::Orientation::HORIZONTAL);
    paned->set_position(240);
    paned->set_hexpand(true);
    paned->set_vexpand(true);
    paned->set_shrink_start_child(false);
    paned->set_shrink_end_child(false);

    auto list_scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    list_scrolled->set_policy(
        Gtk::PolicyType::NEVER, Gtk::PolicyType::AUTOMATIC);
    auto list = Gtk::make_managed<Gtk::ListBox>();
    list->set_selection_mode(Gtk::SelectionMode::NONE);
    list->add_css_class("topic-list");
    list_scrolled->set_child(*list);

    auto compare_scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    compare_scrolled->set_policy(
        Gtk::PolicyType::NEVER, Gtk::PolicyType::AUTOMATIC);
    compare_scrolled->set_hexpand(true);
    compare_scrolled->set_vexpand(true);
    auto compare_box = Gtk::make_managed<Gtk::Box>(
        Gtk::Orientation::HORIZONTAL, 12);
    compare_box->set_hexpand(true);
    compare_box->set_vexpand(true);
    compare_scrolled->set_child(*compare_box);

    // 选中恰好 2 条记录时才可用；只在配置了至少一个 AI 服务商 Key 时才
    // 创建这个按钮，未配置就不出现，不留一个必然点不通的死按钮。
    Gtk::Button* diff_button = nullptr;
    const string ark_api_key =
        resolve_api_key(kSettingArkApiKey, "ATHENA_ARK_API_KEY");
    const string deepseek_api_key =
        resolve_api_key(kSettingDeepseekApiKey, "ATHENA_DEEPSEEK_API_KEY");
    if (!ark_api_key.empty() || !deepseek_api_key.empty()) {
        diff_button = Gtk::make_managed<Gtk::Button>("AI 讲解差异");
        diff_button->add_css_class("btn-sm");
        diff_button->add_css_class("btn-ai-accent");
        diff_button->set_sensitive(false);
        diff_button->set_tooltip_text(
            "选中恰好 2 条记录后可用，让 AI 解释两次运行的源码与输出差异"
            "（优先豆包，失败或未配置时用 DeepSeek）");
    }

    if (runs.empty()) {
        auto empty_row = Gtk::make_managed<Gtk::ListBoxRow>();
        empty_row->set_selectable(false);
        auto empty_label =
            Gtk::make_managed<Gtk::Label>("该知识点还没有运行记录。");
        empty_label->add_css_class("dim-label");
        empty_label->set_margin_top(10);
        empty_label->set_margin_bottom(10);
        empty_label->set_margin_start(10);
        empty_label->set_margin_end(10);
        empty_row->set_child(*empty_label);
        list->append(*empty_row);
    } else {
        // 一次最多选中 2 条记录对比，源码（GtkSourceView，只读高亮）和
        // 输出并排展示；默认选中最近两次运行，省得每次都要手动挑。
        auto run_by_row = make_shared<std::map<Gtk::ListBoxRow*, RunRecord>>();
        auto row_order = make_shared<vector<Gtk::ListBoxRow*>>();
        for (const auto& run : runs) {
            string code_state = "代码版本未知";
            if (!run.source_snapshot.empty() && !current_snapshot.empty()) {
                code_state = run.source_snapshot == current_snapshot
                    ? "代码一致"
                    : "代码已修改";
            }
            const string git_tag = format_git_tag(run);
            auto row = Gtk::make_managed<Gtk::ListBoxRow>();
            row->set_activatable(true);
            row->add_css_class("topic-row");
            auto label = Gtk::make_managed<Gtk::Label>(
                format_timestamp(run.ran_at) + " · "
                + format_duration_ms(run.duration_ms) + " · " + code_state
                + (git_tag.empty() ? "" : " · " + git_tag));
            label->add_css_class("history-row-label");
            label->set_halign(Gtk::Align::START);
            label->set_margin_top(6);
            label->set_margin_bottom(6);
            label->set_margin_start(10);
            label->set_margin_end(10);
            row->set_child(*label);
            (*run_by_row)[row] = run;
            row_order->push_back(row);
            list->append(*row);
        }

        auto selected = make_shared<vector<Gtk::ListBoxRow*>>();

        auto rebuild_compare = make_shared<function<void()>>();
        *rebuild_compare =
            [compare_box, selected, run_by_row, current_snapshot, diff_button]() {
            if (diff_button) {
                diff_button->set_sensitive(selected->size() == 2);
            }
            while (auto* child = compare_box->get_first_child()) {
                compare_box->remove(*child);
            }
            if (selected->empty()) {
                auto hint = Gtk::make_managed<Gtk::Label>(
                    "在左侧点选 1-2 条记录，查看当时的源码快照和输出。");
                hint->add_css_class("dim-label");
                hint->set_valign(Gtk::Align::CENTER);
                hint->set_hexpand(true);
                compare_box->append(*hint);
                return;
            }
            for (auto* row : *selected) {
                const auto found = run_by_row->find(row);
                if (found == run_by_row->end()) {
                    continue;
                }
                const RunRecord& run = found->second;

                auto column = Gtk::make_managed<Gtk::Box>(
                    Gtk::Orientation::VERTICAL, 8);
                column->set_hexpand(true);
                column->set_vexpand(true);

                auto header = Gtk::make_managed<Gtk::Label>(
                    format_timestamp(run.ran_at) + " · "
                    + format_duration_ms(run.duration_ms) + " · "
                    + format_git_summary(run));
                header->set_halign(Gtk::Align::START);
                header->add_css_class("history-compare-heading");
                column->append(*header);

                auto source_frame = Gtk::make_managed<Gtk::Frame>();
                source_frame->set_label("源码快照");
                source_frame->add_css_class("panel-frame");
                source_frame->add_css_class("group-frame");
                source_frame->set_vexpand(true);
                auto source_scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
                source_scrolled->set_vexpand(true);
                auto* raw_source_view = GTK_SOURCE_VIEW(gtk_source_view_new());
                gtk_text_view_set_editable(
                    GTK_TEXT_VIEW(raw_source_view), FALSE);
                gtk_text_view_set_cursor_visible(
                    GTK_TEXT_VIEW(raw_source_view), FALSE);
                gtk_text_view_set_monospace(
                    GTK_TEXT_VIEW(raw_source_view), TRUE);
                gtk_source_view_set_show_line_numbers(raw_source_view, TRUE);
                configure_snapshot_source_view(
                    raw_source_view, run.source_snapshot);
                auto* source_widget =
                    Glib::wrap(GTK_WIDGET(raw_source_view));
                source_widget->add_css_class("code-view");
                source_widget->add_css_class("ai-dialog-text");
                source_scrolled->set_child(*source_widget);
                source_frame->set_child(*source_scrolled);
                column->append(*source_frame);

                auto output_frame = Gtk::make_managed<Gtk::Frame>();
                output_frame->set_label("输出结果");
                output_frame->add_css_class("panel-frame");
                output_frame->add_css_class("group-frame");
                output_frame->set_vexpand(true);
                auto output_scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
                output_scrolled->set_vexpand(true);
                auto output_view = Gtk::make_managed<Gtk::TextView>();
                output_view->set_editable(false);
                output_view->set_cursor_visible(false);
                output_view->set_wrap_mode(Gtk::WrapMode::WORD_CHAR);
                output_view->add_css_class("code-view");
                output_view->add_css_class("ai-dialog-text");
                output_view->get_buffer()->set_text(run.output);
                output_scrolled->set_child(*output_view);
                output_frame->set_child(*output_scrolled);
                column->append(*output_frame);

                compare_box->append(*column);
            }
        };

        auto toggle_row = make_shared<function<void(Gtk::ListBoxRow*)>>();
        *toggle_row = [selected, rebuild_compare](Gtk::ListBoxRow* row) {
            auto found = find(selected->begin(), selected->end(), row);
            if (found != selected->end()) {
                row->remove_css_class("topic-active");
                selected->erase(found);
            } else {
                if (selected->size() >= 2) {
                    auto* oldest = selected->front();
                    oldest->remove_css_class("topic-active");
                    selected->erase(selected->begin());
                }
                row->add_css_class("topic-active");
                selected->push_back(row);
            }
            (*rebuild_compare)();
        };
        list->signal_row_activated().connect(
            [toggle_row](Gtk::ListBoxRow* row) { (*toggle_row)(row); });

        // 默认选中最近两次运行（row_order 按时间倒序排列）。
        if (!row_order->empty()) {
            (*toggle_row)(row_order->at(0));
        }
        if (row_order->size() > 1) {
            (*toggle_row)(row_order->at(1));
        }

        if (diff_button) {
            diff_button->signal_clicked().connect(
                [this, selected, run_by_row, topic_title, ark_api_key,
                 deepseek_api_key]() {
                    if (selected->size() != 2) {
                        return;
                    }
                    const RunRecord& run_a = run_by_row->at(selected->at(0));
                    const RunRecord& run_b = run_by_row->at(selected->at(1));
                    const string prompt =
                        "以下是知识点「" + topic_title + "」两次运行的源码快照"
                        "和输出，请指出源码具体改了什么、这些改动导致了输出上"
                        "什么变化。" + string(kChineseTutorialStyleHint)
                        + "\n\n=== 运行 A（"
                        + format_timestamp(run_a.ran_at) + "）源码 ===\n"
                        + run_a.source_snapshot + "\n\n=== 运行 A 输出 ===\n"
                        + run_a.output + "\n\n=== 运行 B（"
                        + format_timestamp(run_b.ran_at) + "）源码 ===\n"
                        + run_b.source_snapshot + "\n\n=== 运行 B 输出 ===\n"
                        + run_b.output;
                    show_ai_response(
                        "AI 讲解差异：" + topic_title, prompt, ark_api_key,
                        deepseek_api_key);
                });
        }
    }

    paned->set_start_child(*list_scrolled);
    paned->set_end_child(*compare_scrolled);
    content->append(*paned);

    // “AI 讲解差异”底部居中；未配置 Key 时 diff_button 是 nullptr，不
    // 显示这一行。系统对话框自带原生关闭按钮，不再额外加“关闭”。
    if (diff_button) {
        append_dialog_action_bar(content, {diff_button});
    }
    lock_for_modal_dialog(m_parent, *dialog);
}

// 打开对话框，异步用给定提示词调用 AI（优先火山方舟豆包，失败或未配置
// 再退回 DeepSeek），结果当 Markdown 解析后用跟手册页面一样的排版显示：md4c
// 转 HTML、WKWebView（macOS）渲染，代码块、标题、列表都有正常版式，
// 不是纯文本 TextView 堆一坨——AI 的回答经常代码和说明夹杂，纯文本对
// 代码不友好。网络请求在独立线程执行，HTML 只在主线程构造和加载；
// article_view 在对话框隐藏时显式 reset，跟对话框同生命周期。运行历史
// 的“AI 讲解差异”用这个对话框。
void LearningDialogs::show_ai_markdown(
    const string& dialog_title,
    const string& prompt,
    const string& ark_api_key,
    const string& deepseek_api_key,
    const string& loading_markdown,
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


    auto dialog_alive = make_shared<atomic_bool>(true);
    auto article_view = make_shared<unique_ptr<ArticleView>>();
    dialog->signal_hide().connect([dialog_alive, article_view]() {
        dialog_alive->store(false);
        article_view->reset();
    });
    lock_for_modal_dialog(m_parent, *dialog);

    // 只在这几个 AI 对话框里把正文字号调大，不改 resources/article.css
    // 本身——手册阅读页面用原来的 19px，不受影响。
    string stylesheet = m_content_loader.load_resource("/app/article.css");
    if (!stylesheet.empty()) {
        stylesheet += "\n:root { --article-font-size: 22px; }\n";
    }
    *article_view = create_platform_article_view(*article_host, *dialog);
    if (*article_view && !stylesheet.empty()) {
        (*article_view)->load_html(
            render_markdown_html(
                loading_markdown,
                stylesheet,
                parse_markdown_headings(loading_markdown)),
            ATHENA_SOURCE_ROOT);
    }

    auto alive = m_ui_alive;
    thread([alive, dialog_alive, article_view, stylesheet, ark_api_key,
            deepseek_api_key, prompt, dialog]() {
        const AiChatResult result = AiService().chat(
            {.ark_api_key = ark_api_key,
             .deepseek_api_key = deepseek_api_key},
            prompt);
        Glib::signal_idle().connect_once(
            [alive, dialog_alive, article_view, stylesheet, result, dialog]() {
                if (!alive->load() || !dialog_alive->load() || !*article_view
                    || stylesheet.empty()) {
                    return;
                }
                const string markdown =
                    result.ok ? result.content : ("# 请求失败\n\n" + result.error);
                (*article_view)->load_html(
                    render_markdown_html(
                        markdown, stylesheet, parse_markdown_headings(markdown)),
                    ATHENA_SOURCE_ROOT);
                // 网络请求期间用户可能点过主窗口；结果到达时重新前置一次，
                // 不指望等待开始时的那次 present() 全程保持有效。
                dialog->present();
            });
    }).detach();
}

void LearningDialogs::show_ai_response(
    const string& dialog_title,
    const string& prompt,
    const string& ark_api_key,
    const string& deepseek_api_key) {
    show_ai_markdown(
        dialog_title, prompt, ark_api_key, deepseek_api_key,
        "正在请求 AI，请稍候…", 760, 620);
}

// 打开对话框，异步向 AI（优先火山方舟豆包，失败或未配置再退回 DeepSeek）请求
// 针对该知识点具体源码的选择题（JSON 格式，每题含题干、选项、正确选项
// 下标和解释），逐题展示；每题先选一个选项，点“提交答案”才判对错、给
// 解释，颜色区分对错。返回的 JSON 解析失败时退化为纯文本展示，不崩溃、
// 不隐藏结果。
void LearningDialogs::show_quiz(
    const DialogTopic& topic,
    function<bool(int)> on_mastery_changed) {
    const string ark_api_key =
        resolve_api_key(kSettingArkApiKey, "ATHENA_ARK_API_KEY");
    const string deepseek_api_key =
        resolve_api_key(kSettingDeepseekApiKey, "ATHENA_DEEPSEEK_API_KEY");
    if (ark_api_key.empty() && deepseek_api_key.empty()) {
        auto notice = Gtk::make_managed<Gtk::MessageDialog>(
            m_parent,
            "自测功能需要先在侧边栏底部“设置”里配置至少一个 AI "
            "服务商 Key",
            false,
            Gtk::MessageType::INFO,
            Gtk::ButtonsType::OK,
            true);
        notice->signal_response().connect([notice](int) { notice->hide(); });
        notice->show();
        return;
    }

    const string function_id = topic.function_id;
    const string topic_title = topic.title;
    string prompt =
        "请为 C++ 知识点「" + topic_title + "」生成一次可量化的掌握度自测。"
        "只能考察下面的知识点说明和参考实现能够支持的内容，不考范围外的"
        "冷门标准条款、编译器细节或文字陷阱。出题前先在内部列出独立考察"
        "点，确保核心语义、源码中的关键行为以及常见误用或边界情况都至少"
        "被一道题覆盖，但不要输出这份内部列表。题目数量由独立考察点的实际"
        "数量决定，少于 5 道或多于 5 道都可以，覆盖完整后立即停止；不要把"
        "同一事实换一种说法重复出题。优先使用短小、完整、可以实际分析的"
        "C++ 代码场景：例如判断输出或编译结果、跟踪对象和资源生命周期、"
        "识别所有权或异常安全问题、选择正确修改方案。能用代码场景考察的"
        "内容就不要改成纯定义背诵或措辞辩论；只有确实无法通过短代码表达"
        "时，才使用少量必要的概念题。只在知识点本身确有相关内容时考察边界"
        "与易错点；代码场景不得依赖未定义行为、特定编译器偶然表现或题目中"
        "没有说明的平台差异。"
        "不要用超出当前知识点范围的内容人为提高难度。每道题必须有能够由"
        "源码或明确 C++ 规则支持的答案，干扰项要合理但不能含糊。每题选项"
        "数量按题目需要决定；大多数题只有一个正确答案，确实有多个正确项"
        "时才做成多选题，并在 correct_indices 中列出全部正确选项。解释要"
        "简短说明正确依据及主要干扰项错在哪里。代码场景题把共享代码放进"
        "code 字段，不加 Markdown 代码围栏；不需要代码的题将 code 省略或"
        "设为空字符串。只用 JSON 格式返回，形如 "
        "{\"questions\":[{\"question\":"
        "\"...\",\"code\":\"...\",\"options\":[\"...\",\"...\"],"
        "\"correct_indices\":[0],"
        "\"explanation\":\"...\"}]}，correct_indices 是从 0 开始的正确"
        "选项下标数组，单选题这个数组只有一个元素。解释文字的" +
        string(kChineseTutorialStyleHint) +
        " 不要输出 JSON 之外的任何文字。\n\n知识点说明：" + topic.description;
    const auto body = load_member_source_text(
        m_content_loader, topic.source_path, topic.member_name);
    if (body && !body->empty()) {
        prompt += "\n\n参考实现：\n" + *body;
    }

    auto dialog = new Gtk::Dialog();
    dialog->set_title("知识点自测：" + topic_title);
    dialog->set_default_size(680, 560);

    auto* content = dialog->get_content_area();
    auto scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    scrolled->set_hexpand(true);
    scrolled->set_vexpand(true);
    auto quiz_box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 16);
    quiz_box->set_margin_top(8);
    quiz_box->set_margin_bottom(8);
    quiz_box->set_margin_start(8);
    quiz_box->set_margin_end(8);
    auto loading_label = Gtk::make_managed<Gtk::Label>("正在生成自测题，请稍候…");
    loading_label->add_css_class("dim-label");
    loading_label->add_css_class("ai-dialog-option");
    quiz_box->append(*loading_label);
    scrolled->set_child(*quiz_box);
    content->append(*scrolled);


    auto dialog_alive = make_shared<atomic_bool>(true);
    dialog->signal_hide().connect([dialog_alive]() { dialog_alive->store(false); });
    lock_for_modal_dialog(m_parent, *dialog);

    auto alive = m_ui_alive;
    thread([alive, dialog_alive, quiz_box, ark_api_key, deepseek_api_key, prompt,
            dialog, function_id, on_mastery_changed]() {
        const AiChatResult result = AiService().chat(
            {.ark_api_key = ark_api_key,
             .deepseek_api_key = deepseek_api_key},
            prompt);
        Glib::signal_idle().connect_once(
            [alive, dialog_alive, quiz_box, result, dialog, function_id,
             on_mastery_changed]() {
                if (!alive->load() || !dialog_alive->load()) {
                    return;
                }
                // 网络请求期间用户可能点过主窗口；结果到达时（不管题目
                // 是否解析成功）重新前置一次，不指望等待开始时的那次
                // present() 全程保持有效。
                dialog->present();
                while (auto* child = quiz_box->get_first_child()) {
                    quiz_box->remove(*child);
                }
                if (!result.ok) {
                    auto error_label = Gtk::make_managed<Gtk::Label>(
                        "请求失败：" + result.error);
                    error_label->set_halign(Gtk::Align::START);
                    error_label->set_wrap(true);
                    error_label->add_css_class("ai-dialog-option");
                    quiz_box->append(*error_label);
                    return;
                }

                const auto quiz = parse_ai_quiz_response(result.content);
                const bool parsed_ok = quiz.has_value();
                if (quiz) {
                    const int total_questions =
                        static_cast<int>(quiz->questions.size());
                    auto answered_questions = make_shared<int>(0);
                    auto correct_answers = make_shared<int>(0);
                    auto score_label = Gtk::make_managed<Gtk::Label>(
                        "完成全部 " + to_string(total_questions)
                        + " 道题后，将按本次成绩自动更新熟练度");
                    score_label->set_halign(Gtk::Align::START);
                    score_label->set_wrap(true);
                    score_label->set_xalign(0);
                    score_label->add_css_class("ai-dialog-feedback");
                    quiz_box->append(*score_label);

                    for (const auto& item : quiz->questions) {
                        const string question = item.question;
                        const string code = item.code;
                        const vector<string> options = item.options;
                        const vector<int> correct_indices = item.correct_indices;
                        const string explanation = item.explanation;
                        const bool is_multi_select = correct_indices.size() > 1;

                        auto item_box = Gtk::make_managed<Gtk::Box>(
                            Gtk::Orientation::VERTICAL, 8);

                        auto question_label = Gtk::make_managed<Gtk::Label>(
                            question
                            + (is_multi_select ? "（多选）" : ""));
                        question_label->set_halign(Gtk::Align::START);
                        question_label->set_wrap(true);
                        question_label->set_xalign(0);
                        question_label->add_css_class("ai-dialog-question");
                        item_box->append(*question_label);

                        if (!code.empty()) {
                            auto code_scrolled =
                                Gtk::make_managed<Gtk::ScrolledWindow>();
                            code_scrolled->set_policy(
                                Gtk::PolicyType::AUTOMATIC,
                                Gtk::PolicyType::NEVER);
                            const int line_count = static_cast<int>(
                                count(code.begin(), code.end(), '\n') + 1);
                            code_scrolled->set_min_content_height(
                                clamp(line_count * 28 + 20, 76, 272));
                            code_scrolled->add_css_class("ai-quiz-code-frame");

                            auto code_view =
                                Gtk::make_managed<Gtk::TextView>();
                            code_view->set_editable(false);
                            code_view->set_cursor_visible(false);
                            code_view->set_monospace(true);
                            code_view->set_wrap_mode(Gtk::WrapMode::NONE);
                            code_view->get_buffer()->set_text(code);
                            code_view->add_css_class("ai-quiz-code");
                            code_scrolled->set_child(*code_view);
                            item_box->append(*code_scrolled);
                        }

                        // 单选题的选项分到同一个 group（互斥，radio 行为）；
                        // 多选题的选项各自独立、可以同时勾选多个。
                        auto option_buttons =
                            make_shared<vector<Gtk::CheckButton*>>();
                        Gtk::CheckButton* first_option = nullptr;
                        for (const auto& option_text : options) {
                            auto option = Gtk::make_managed<Gtk::CheckButton>(
                                option_text);
                            option->add_css_class("ai-dialog-option");
                            if (!is_multi_select) {
                                if (first_option) {
                                    option->set_group(*first_option);
                                } else {
                                    first_option = option;
                                }
                            }
                            option_buttons->push_back(option);
                            item_box->append(*option);
                        }

                        auto feedback_label = Gtk::make_managed<Gtk::Label>();
                        feedback_label->set_halign(Gtk::Align::START);
                        feedback_label->set_wrap(true);
                        feedback_label->set_xalign(0);
                        feedback_label->add_css_class("ai-dialog-feedback");
                        feedback_label->set_visible(false);

                        auto explanation_label =
                            Gtk::make_managed<Gtk::Label>(explanation);
                        explanation_label->set_halign(Gtk::Align::START);
                        explanation_label->set_wrap(true);
                        explanation_label->set_xalign(0);
                        explanation_label->add_css_class("ai-dialog-explanation");
                        explanation_label->set_visible(false);

                        auto submit_button =
                            Gtk::make_managed<Gtk::Button>("提交答案");
                        submit_button->add_css_class("btn-sm");
                        submit_button->add_css_class("btn-ai-accent");
                        submit_button->set_halign(Gtk::Align::START);
                        submit_button->signal_clicked().connect(
                            [option_buttons,
                             correct_indices,
                             options,
                             feedback_label,
                             explanation_label,
                             submit_button,
                             answered_questions,
                             correct_answers,
                             total_questions,
                             score_label,
                             function_id,
                             on_mastery_changed]() {
                                vector<int> selected_indices;
                                for (size_t index = 0;
                                     index < option_buttons->size();
                                     ++index) {
                                    if ((*option_buttons)[index]->get_active()) {
                                        selected_indices.push_back(
                                            static_cast<int>(index));
                                    }
                                }
                                if (selected_indices.empty()) {
                                    feedback_label->set_text("请先选至少一个选项");
                                    feedback_label->remove_css_class("correct");
                                    feedback_label->remove_css_class("incorrect");
                                    feedback_label->set_visible(true);
                                    return;
                                }
                                // 多选题要求选中集合与正确答案集合完全一致
                                // 才算对，不给部分分。
                                auto sorted_selected = selected_indices;
                                auto sorted_correct = correct_indices;
                                sort(sorted_selected.begin(), sorted_selected.end());
                                sort(sorted_correct.begin(), sorted_correct.end());
                                const bool is_correct =
                                    sorted_selected == sorted_correct;
                                if (is_correct) {
                                    ++*correct_answers;
                                    feedback_label->set_text("✓ 回答正确");
                                } else {
                                    string correct_text;
                                    for (int index : sorted_correct) {
                                        if (!correct_text.empty()) {
                                            correct_text += "、";
                                        }
                                        correct_text +=
                                            options[static_cast<size_t>(index)];
                                    }
                                    feedback_label->set_text(
                                        "✗ 回答错误，正确答案是：" + correct_text);
                                }
                                feedback_label->remove_css_class("correct");
                                feedback_label->remove_css_class("incorrect");
                                feedback_label->add_css_class(
                                    is_correct ? "correct" : "incorrect");
                                feedback_label->set_visible(true);
                                explanation_label->set_visible(true);
                                for (auto* option : *option_buttons) {
                                    option->set_sensitive(false);
                                }
                                submit_button->set_sensitive(false);

                                ++*answered_questions;
                                if (*answered_questions == total_questions) {
                                    const int mastery = mastery_from_quiz_score(
                                        *correct_answers, total_questions);
                                    const bool saved =
                                        on_mastery_changed(mastery);
                                    score_label->set_text(
                                        "本次成绩：" + to_string(*correct_answers)
                                        + "/" + to_string(total_questions)
                                        + "，自动评定为 " + to_string(mastery)
                                        + " 星。"
                                        + (saved
                                               ? "评分已保存到学习进度。"
                                               : "评分暂时无法保存。"));
                                    if (mastery >= 5) {
                                        score_label->add_css_class("correct");
                                    }
                                    score_label->set_tooltip_text(
                                        "知识点 " + function_id
                                        + "：按正确率 × 5 向下取整；只有全对才是 5 星");
                                }
                            });
                        item_box->append(*submit_button);
                        item_box->append(*feedback_label);
                        item_box->append(*explanation_label);

                        quiz_box->append(*item_box);
                        quiz_box->append(*Gtk::make_managed<Gtk::Separator>());
                    }
                }

                if (!parsed_ok) {
                    // AI 没按要求的 JSON 格式返回时，原样展示文本，
                    // 至少不丢内容。
                    auto fallback_label =
                        Gtk::make_managed<Gtk::Label>(result.content);
                    fallback_label->set_halign(Gtk::Align::START);
                    fallback_label->set_wrap(true);
                    fallback_label->add_css_class("ai-dialog-option");
                    quiz_box->append(*fallback_label);
                }
            });
    }).detach();
}
