#include "mainwindow.h"
#include "app_icon.h"
#include "content/source_locator.h"
#include "render/markdown_renderer.h"

#include <gtksourceview/gtksource.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <ctime>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>

using namespace std;

namespace {

string format_elapsed(double seconds) {
    ostringstream stream;
    stream << fixed << setprecision(2) << seconds << "s";
    return stream.str();
}

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

// 提取知识点成员函数的完整源码文本。
optional<string> member_source_body(
    const ContentLoader& loader,
    const string& source_path,
    const string& member_name) {
    try {
        const string source = loader.load_project_file(source_path);
        const auto range = locate_cpp_member_function(source, member_name);
        if (!range) {
            return nullopt;
        }
        return source.substr(range->begin, range->end - range->begin);
    } catch (const exception&) {
        return nullopt;
    }
}

struct GitSourceState {
    string commit;    // HEAD 短哈希；不在 git 仓库或 git 不可用时为空
    bool dirty = false;
};

// 查询源文件在 ATHENA_SOURCE_ROOT 这个 git 仓库中的运行时版本：HEAD 短
// 哈希，以及该文件相对 HEAD 是否有未提交改动。不在 git 仓库、没装 git
// 或命令失败时静默返回空结果，调用方据此退回“版本未知”，不影响运行。
GitSourceState query_git_source_state(const string& relative_path) {
    GitSourceState state;
    if (relative_path.empty()) {
        return state;
    }
    try {
        const string root = ATHENA_SOURCE_ROOT;
        string commit_output;
        int exit_status = 0;
        const string commit_command =
            "git -C " + Glib::shell_quote(root) + " rev-parse --short HEAD";
        Glib::spawn_command_line_sync(
            commit_command, &commit_output, nullptr, &exit_status);
        if (exit_status != 0) {
            return state;
        }
        while (!commit_output.empty()
               && (commit_output.back() == '\n' || commit_output.back() == '\r')) {
            commit_output.pop_back();
        }
        if (commit_output.empty()) {
            return state;
        }
        state.commit = commit_output;

        string status_output;
        exit_status = 0;
        const string status_command = "git -C " + Glib::shell_quote(root)
            + " status --porcelain -- " + Glib::shell_quote(relative_path);
        Glib::spawn_command_line_sync(
            status_command, &status_output, nullptr, &exit_status);
        if (exit_status == 0) {
            state.dirty = !status_output.empty();
        }
    } catch (const exception& error) {
        cerr << "Failed to query git state: " << error.what() << endl;
        return GitSourceState {};
    }
    return state;
}

// 把提示词放入剪贴板并唤起本机 AI 助手；豆包客户端支持 doubao:// 协议
// 但不支持携带提示词参数，因此采用“剪贴板 + 唤起”的组合；默认命令可用
// 环境变量 ATHENA_AI_COMMAND 自定义。供知识点解释和章节总纲共用。
void copy_prompt_and_launch_ai(const string& prompt) {
    Gdk::Display::get_default()->get_clipboard()->set_text(prompt);

    string command = "open doubao://";
    if (const char* custom = g_getenv("ATHENA_AI_COMMAND")) {
        command = custom;
    }
    try {
        Glib::spawn_command_line_async(command);
    } catch (const exception& error) {
        cerr << "Failed to launch AI assistant (" << command
             << "): " << error.what() << endl;
    }
}

// 把知识点说明与源码组成解释请求复制到剪贴板，并唤起本机 AI 助手。
void explain_with_local_ai(
    const ContentLoader& loader,
    const string& title,
    const string& description,
    const string& source_path,
    const string& member_name) {
    string prompt = "请解释 C++ 知识点「" + title + "」：" + description;
    const auto body = member_source_body(loader, source_path, member_name);
    if (body && !body->empty()) {
        prompt += "\n\n参考实现：\n" + *body;
    }
    copy_prompt_and_launch_ai(prompt);
}

// 把章节标题、简介与全部知识点标题/说明组成总纲请求复制到剪贴板，并唤起
// 本机 AI 助手；不依赖当前是否选中了具体知识点。
void explain_chapter_overview_with_local_ai(
    const string& title,
    const string& description,
    const vector<SubChapter>& subchapters) {
    string prompt = "请给出 C++ 章节「" + title + "」的学习总纲：" + description;
    if (!subchapters.empty()) {
        prompt += "\n\n本章知识点：";
        for (const auto& sub : subchapters) {
            prompt += "\n- " + sub.title + "：" + sub.description;
        }
    }
    copy_prompt_and_launch_ai(prompt);
}

void display_source(
    GtkSourceView* source_view,
    const ContentLoader& content_loader,
    const string& relative_path,
    const string& member_name = "") {
    if (!source_view) {
        return;
    }

    string source_text;
    if (!relative_path.empty()) {
        source_text = content_loader.load_project_file(relative_path);
    }
    if (source_text.empty()) {
        source_text = relative_path.empty()
            ? "该知识点尚未添加实验源码。"
            : "无法读取源文件：" + relative_path;
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

    auto text_buffer = GTK_TEXT_BUFFER(source_buffer);
    gtk_text_buffer_set_text(
        text_buffer,
        source_text.c_str(),
        static_cast<int>(source_text.size()));

    GtkTextIter source_begin;
    gtk_text_buffer_get_start_iter(text_buffer, &source_begin);
    gtk_text_buffer_place_cursor(text_buffer, &source_begin);

    const auto source_range = locate_cpp_member_function(
        source_text,
        member_name);
    if (!source_range) {
        return;
    }

    GtkTextIter highlight_begin;
    GtkTextIter highlight_end;
    gtk_text_buffer_get_iter_at_offset(
        text_buffer,
        &highlight_begin,
        static_cast<int>(g_utf8_pointer_to_offset(
            source_text.c_str(),
            source_text.c_str() + source_range->begin)));
    gtk_text_buffer_get_iter_at_offset(
        text_buffer,
        &highlight_end,
        static_cast<int>(g_utf8_pointer_to_offset(
            source_text.c_str(),
            source_text.c_str() + source_range->end)));

    auto tag_table = gtk_text_buffer_get_tag_table(text_buffer);
    auto highlight_tag = gtk_text_tag_table_lookup(
        tag_table,
        "athena-topic-highlight");
    if (!highlight_tag) {
        highlight_tag = gtk_text_buffer_create_tag(
            text_buffer,
            "athena-topic-highlight",
            "background",
            "#dbeafe",
            nullptr);
    }
    gtk_text_buffer_apply_tag(
        text_buffer,
        highlight_tag,
        &highlight_begin,
        &highlight_end);
    gtk_text_buffer_place_cursor(text_buffer, &highlight_begin);
    gtk_text_view_scroll_to_iter(
        GTK_TEXT_VIEW(source_view),
        &highlight_begin,
        0.15,
        true,
        0.0,
        0.20);
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

string chapter_key(const string& category_name, const string& chapter_name) {
    return category_name + "." + chapter_name;
}

const ChapterGroup* find_group(const ChapterMeta& chapter, const string& name) {
    auto found = find_if(
        chapter.groups.begin(),
        chapter.groups.end(),
        [&name](const ChapterGroup& group) { return group.name == name; });
    return found == chapter.groups.end() ? nullptr : &*found;
}

struct TopicSelection {
    string description;
    string source_path;
    string member_name;
    string title;
    string function_id;
    IconSpec icon;
};

} // namespace

MainWindow::MainWindow(
    BaseObjectType* cobject,
    const Glib::RefPtr<Gtk::Builder>& builder)
    : Gtk::ApplicationWindow(cobject),
      m_main_builder(builder),
      m_content_loader(ATHENA_SOURCE_ROOT),
      m_function_registry(create_default_function_registry()) {
    maximize();
    apply_runtime_application_icon();

    auto css = Gtk::CssProvider::create();
    css->load_from_resource("/app/style.css");
    Gtk::StyleContext::add_provider_for_display(
        get_display(),
        css,
        GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

    // 任务栏/窗口图标：从 GResource 的图标主题结构解析 cn.athena.icon。
    Gtk::IconTheme::get_for_display(get_display())
        ->add_resource_path("/app/icons");
    Gtk::Window::set_default_icon_name("cn.athena.icon");

    m_category_sidebar = m_main_builder->get_widget<Gtk::Box>("category_sidebar");
    m_chapter_stack = m_main_builder->get_widget<Gtk::Stack>("chapter_stack");
    m_chapter_tab_box = m_main_builder->get_widget<Gtk::FlowBox>("chapter_tab_box");

    if (!m_category_sidebar || !m_chapter_stack || !m_chapter_tab_box) {
        throw runtime_error("Failed to get required widgets from main UI");
    }

    load_chapter_metadata();
    setup_category_sidebar();
    open_learning_store();
}

void MainWindow::load_chapter_metadata() {
    const string source = m_content_loader.load_resource("/app/data/athena.json");
    if (source.empty()) {
        throw runtime_error("athena.json not found in GResource");
    }
    m_catalog = ChapterCatalog::from_json(source);
}

void MainWindow::configure_image(
    Gtk::Image& image,
    const IconSpec& icon,
    int pixel_size) const {
    if (icon.type == "resource" && !icon.path.empty()) {
        string resource_path = icon.path;
        constexpr string_view resources_prefix = "resources/";
        if (resource_path.rfind(resources_prefix, 0) == 0) {
            resource_path = "/app/" + resource_path.substr(resources_prefix.size());
        }
        image.set_from_resource(resource_path);
    } else if (!icon.name.empty()) {
        image.set_from_icon_name(icon.name);
    } else {
        image.set_visible(false);
        return;
    }

    image.set_pixel_size(pixel_size);
}

Gtk::Image* MainWindow::create_icon(const IconSpec& icon, int pixel_size) const {
    auto image = Gtk::make_managed<Gtk::Image>();
    configure_image(*image, icon, pixel_size);
    return image;
}

void MainWindow::setup_category_sidebar() {
    for (const auto& category : m_catalog.categories()) {
        auto button = Gtk::make_managed<Gtk::ToggleButton>();
        button->add_css_class("nav-button");
        button->set_tooltip_text(category.description);

        auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
        box->set_valign(Gtk::Align::CENTER);
        box->set_margin_top(12);
        box->set_margin_bottom(12);

        box->append(*create_icon(category.icon, 24));

        auto label = Gtk::make_managed<Gtk::Label>(category.title);
        label->set_wrap(true);
        label->set_justify(Gtk::Justification::CENTER);
        label->set_max_width_chars(7);
        box->append(*label);
        button->set_child(*box);

        if (!m_category_buttons.empty()) {
            button->set_group(*m_category_buttons.front());
        }

        button->signal_toggled().connect(
            [this, category_name = category.name, button]() {
                if (button->get_active()) {
                    on_category_selected(category_name);
                }
            });

        m_category_sidebar->append(*button);
        m_category_buttons.push_back(button);
    }

    if (!m_category_buttons.empty()) {
        m_category_buttons.front()->set_active(true);
    }
}

void MainWindow::on_category_selected(const string& category_name) {
    if (category_name == m_current_category) {
        return;
    }

    m_current_category = category_name;
    build_chapter_tabs(category_name);
}

// 首次激活章节标签时才构建真实页面（含 WKWebView）；
// 打开分类只挂占位页，避免一次性构建全部章节拖慢启动。
void MainWindow::ensure_chapter_page(
    const string& category_name,
    const ChapterMeta& chapter) {
    const string page_key = chapter_key(category_name, chapter.name);
    if (m_loaded_chapters.find(page_key) != m_loaded_chapters.end()) {
        return;
    }

    const auto builder = get_chapter_builder(category_name, chapter.name);
    if (!builder) {
        cerr << "Failed to create builder for " << page_key << endl;
        return;
    }

    auto widget = builder->get_widget<Gtk::Widget>(chapter.widget_name);
    if (!widget) {
        cerr << "Failed to get root widget '" << chapter.widget_name
             << "' for " << page_key << endl;
        return;
    }

    if (auto* placeholder = m_chapter_stack->get_child_by_name(page_key)) {
        m_chapter_stack->remove(*placeholder);
    }
    m_chapter_stack->add(*widget, page_key, chapter.title);

    const bool uses_article_page = chapter.widget_name == "article_page";
    if (uses_article_page) {
        if (initialize_article_page(page_key, chapter, builder)) {
            m_loaded_chapters.insert(page_key);
        }
        return;
    }

    const bool uses_code_page = chapter.widget_name == "chapter_page";
    if (uses_code_page) {
        initialize_code_page(category_name, chapter, builder);
        m_loaded_chapters.insert(page_key);
        return;
    }

    // 特殊页面（如欢迎页）无需内容初始化，构建控件树即完成。
    m_loaded_chapters.insert(page_key);
}

void MainWindow::build_chapter_tabs(const string& category_name) {
    for (const auto& name : m_active_page_names) {
        if (auto child = m_chapter_stack->get_child_by_name(name)) {
            m_chapter_stack->remove(*child);
        }
    }
    m_active_page_names.clear();

    for (auto* button : m_tab_buttons) {
        m_chapter_tab_box->remove(*button);
    }
    m_tab_buttons.clear();

    const auto& all_chapters = m_catalog.chapters();
    auto category = all_chapters.find(category_name);
    if (category == all_chapters.end() || category->second.empty()) {
        auto placeholder = Gtk::make_managed<Gtk::Label>("该分类暂无章节");
        placeholder->set_halign(Gtk::Align::CENTER);
        placeholder->set_valign(Gtk::Align::CENTER);
        const string empty_key = category_name + ".__empty__";
        m_chapter_stack->add(*placeholder, empty_key, "空");
        m_active_page_names.insert(empty_key);
        return;
    }

    for (const auto& chapter : category->second) {
        const string page_key = chapter_key(category_name, chapter.name);

        // 已构建过的页面直接重新挂载（builder 缓存持有控件树）；
        // 未构建的先挂占位页，首次激活标签时再替换为真实页面。
        const bool already_built =
            m_loaded_chapters.find(page_key) != m_loaded_chapters.end();
        if (already_built) {
            const auto builder =
                get_chapter_builder(category_name, chapter.name);
            auto widget = builder
                ? builder->get_widget<Gtk::Widget>(chapter.widget_name)
                : nullptr;
            if (!widget) {
                cerr << "Failed to get root widget '" << chapter.widget_name
                     << "' for " << page_key << endl;
                continue;
            }
            m_chapter_stack->add(*widget, page_key, chapter.title);
        } else {
            auto placeholder = Gtk::make_managed<Gtk::Box>();
            m_chapter_stack->add(*placeholder, page_key, chapter.title);
        }
        m_active_page_names.insert(page_key);

        auto tab_button = Gtk::make_managed<Gtk::ToggleButton>();
        tab_button->add_css_class("pill");
        tab_button->add_css_class("chapter-tab");
        tab_button->set_tooltip_text(chapter.description);

        auto tab_content = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
        tab_content->append(*create_icon(chapter.icon, 16));
        tab_content->append(*Gtk::make_managed<Gtk::Label>(chapter.title));
        tab_button->set_child(*tab_content);

        if (!m_tab_buttons.empty()) {
            tab_button->set_group(*m_tab_buttons.front());
        }

        tab_button->signal_toggled().connect(
            [this, page_key, tab_button, category_name, chapter]() {
                if (!tab_button->get_active()) {
                    return;
                }
                ensure_chapter_page(category_name, chapter);
                if (auto* child = m_chapter_stack->get_child_by_name(page_key)) {
                    m_chapter_stack->set_visible_child(*child);
                }
                m_current_chapter = page_key;
            });

        m_chapter_tab_box->append(*tab_button);
        m_tab_buttons.push_back(tab_button);
    }

    if (!m_tab_buttons.empty()) {
        m_tab_buttons.front()->set_active(true);
    }
}

bool MainWindow::initialize_article_page(
    const string& page_key,
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder) {
    auto article_web_host =
        builder->get_widget<Gtk::DrawingArea>("article_web_host");
    if (!article_web_host) {
        cerr << "Article page is missing its WebView host for "
             << page_key << endl;
        return false;
    }

    const string markdown = m_content_loader.load_document(chapter.document);
    if (markdown.empty()) {
        cerr << "Failed to load article document for " << page_key
             << ": " << chapter.document << endl;
        return true;
    }

    try {
        const auto headings = parse_markdown_headings(markdown);
        const string stylesheet =
            m_content_loader.load_resource("/app/article.css");
        if (stylesheet.empty()) {
            throw runtime_error("Article stylesheet is unavailable");
        }

        auto view = create_platform_article_view(
            *article_web_host,
            *this);
        if (!view) {
            throw runtime_error("No WebView backend is available");
        }
        view->load_html(
            render_markdown_html(markdown, stylesheet, headings),
            m_content_loader.document_base_directory(chapter.document));
        m_article_views[page_key] = std::move(view);
    } catch (const exception& error) {
        cerr << "Failed to render article for " << page_key
             << ": " << error.what() << endl;
    }
    return true;
}

void MainWindow::initialize_code_page(
    const string& category_name,
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder) {
    auto title_label = builder->get_widget<Gtk::Label>("chapter_title_label");
    auto description_label =
        builder->get_widget<Gtk::Label>("chapter_description_label");
    auto chapter_icon = builder->get_widget<Gtk::Image>("chapter_icon");
    auto source_view = GTK_SOURCE_VIEW(
        gtk_builder_get_object(builder->gobj(), "source_view"));
    auto result_view = builder->get_widget<Gtk::TextView>("result_view");
    auto topics_list = builder->get_widget<Gtk::ListBox>("topics_list");
    auto knowledge_description_label =
        builder->get_widget<Gtk::Label>("knowledge_description_label");

    if (title_label) {
        title_label->set_text(chapter.title);
    }
    if (description_label) {
        description_label->set_text(chapter.description);
    }
    if (chapter_icon) {
        configure_image(*chapter_icon, chapter.icon, 36);
    }

    display_source(source_view, m_content_loader, chapter.source);

    if (result_view) {
        auto result_buffer = result_view->get_buffer();
        result_buffer->set_text("点击右侧知识点即可运行实验并在此查看结果。");
        auto result_begin = result_buffer->begin();
        result_buffer->place_cursor(result_begin);
    }

    auto experiment_spinner =
        builder->get_widget<Gtk::Spinner>("experiment_spinner");
    auto experiment_status_label =
        builder->get_widget<Gtk::Label>("experiment_status_label");
    auto note_view = builder->get_widget<Gtk::TextView>("note_view");
    auto chapter_overview_button =
        builder->get_widget<Gtk::Button>("chapter_overview_button");

    // 章节总纲不依赖当前选中的知识点，常驻可点，独立于知识点列表接线。
    if (chapter_overview_button) {
        chapter_overview_button->signal_clicked().connect(
            [title = chapter.title,
             description = chapter.description,
             subchapters = chapter.subchapters]() {
                explain_chapter_overview_with_local_ai(
                    title, description, subchapters);
            });
    }

    if (topics_list) {
        populate_topic_list(
            category_name,
            chapter,
            source_view,
            result_view,
            *topics_list,
            knowledge_description_label,
            experiment_spinner,
            experiment_status_label,
            title_label,
            description_label,
            chapter_icon,
            note_view);
    }
}

MainWindow::~MainWindow() {
    m_elapsed_timer.disconnect();
    if (m_experiment_thread.joinable()) {
        m_experiment_thread.join();
    }
    // 控件即将销毁：已排队但未执行的回传回调检查该标志后直接跳过。
    m_ui_alive->store(false);
}

void MainWindow::open_learning_store() {
    const string data_dir =
        Glib::build_filename(Glib::get_user_data_dir(), "Athena");
    g_mkdir_with_parents(data_dir.c_str(), 0700);
    try {
        m_learning_store = make_unique<LearningStore>(
            Glib::build_filename(data_dir, "learning.db"));
    } catch (const exception& error) {
        cerr << "Learning store unavailable: " << error.what() << endl;
        m_learning_store.reset();
    }
}

void MainWindow::show_history_dialog(
    const string& function_id,
    const string& source_path,
    const string& member_name,
    const string& topic_title) {
    if (!m_learning_store) {
        return;
    }
    vector<RunRecord> runs;
    try {
        runs = m_learning_store->recent_runs(function_id, 20);
    } catch (const exception& error) {
        cerr << "Failed to load run history for " << function_id << ": "
             << error.what() << endl;
    }
    const string current_snapshot =
        member_source_body(m_content_loader, source_path, member_name)
            .value_or("");

    auto dialog = Gtk::make_managed<Gtk::Dialog>();
    dialog->set_title("运行历史：" + topic_title);
    dialog->set_transient_for(*this);
    dialog->set_modal(true);
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
        *rebuild_compare = [compare_box, selected, run_by_row, current_snapshot]() {
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
                header->add_css_class("heading");
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
    }

    paned->set_start_child(*list_scrolled);
    paned->set_end_child(*compare_scrolled);
    content->append(*paned);

    dialog->add_button("关闭", static_cast<int>(Gtk::ResponseType::CANCEL));
    dialog->signal_response().connect([dialog](int) { dialog->hide(); });
    dialog->show();
}

// 在独立工作线程中执行实验：同一时刻只允许一个实验，
// 运行期间新的运行请求被忽略；结果与耗时经主线程回填。
void MainWindow::start_experiment(
    const string& function_id,
    const string& source_path,
    const string& member_name,
    Gtk::TextView& result_view,
    Gtk::Spinner* experiment_spinner,
    Gtk::Label* experiment_status_label) {
    if (m_experiment_running) {
        return;
    }
    m_experiment_running = true;

    const string source_snapshot =
        member_source_body(m_content_loader, source_path, member_name)
            .value_or("");
    const GitSourceState git_state = query_git_source_state(source_path);

    const auto result_buffer = result_view.get_buffer();
    result_buffer->set_text("运行中…");

    if (experiment_spinner) {
        experiment_spinner->set_visible(true);
        experiment_spinner->set_spinning(true);
    }

    const auto started = chrono::steady_clock::now();
    if (experiment_status_label) {
        experiment_status_label->set_visible(true);
        experiment_status_label->set_text("运行中 · 0.00s");
    }
    m_elapsed_timer.disconnect();
    m_elapsed_timer = Glib::signal_timeout().connect(
        [experiment_status_label, alive = m_ui_alive, started]() -> bool {
            if (!alive->load() || !experiment_status_label) {
                return false;
            }
            const auto elapsed = chrono::duration<double>(
                chrono::steady_clock::now() - started);
            experiment_status_label->set_text(
                "运行中 · " + format_elapsed(elapsed.count()));
            return true;
        },
        200);

    auto alive = m_ui_alive;
    auto* registry = &m_function_registry;
    // 工作线程与回传回调只接触这些主线程成员的指针，回调本身经 alive 标志保护。
    auto* experiment_thread = &m_experiment_thread;
    auto* elapsed_timer = &m_elapsed_timer;
    auto* running_flag = &m_experiment_running;
    auto* learning_store = m_learning_store.get();
    m_experiment_thread = thread(
        [function_id,
         source_snapshot,
         git_state,
         result_buffer,
         experiment_spinner,
         experiment_status_label,
         alive,
         registry,
         experiment_thread,
         elapsed_timer,
         running_flag,
         learning_store,
         started]() {
            ostringstream output;
            string failure;
            try {
                registry->run(function_id, output);
            } catch (const exception& error) {
                failure = "运行失败：" + string(error.what());
            }
            const auto duration = chrono::duration<double>(
                chrono::steady_clock::now() - started);
            const string raw_output = failure.empty() ? output.str() : failure;
            const string result =
                raw_output + "\n—— 耗时 " + format_elapsed(duration.count()) + " ——";
            const double duration_ms = duration.count() * 1000.0;

            Glib::signal_idle().connect_once(
                [function_id,
                 source_snapshot,
                 git_state,
                 raw_output,
                 duration_ms,
                 result_buffer,
                 experiment_spinner,
                 experiment_status_label,
                 alive,
                 result,
                 experiment_thread,
                 elapsed_timer,
                 running_flag,
                 learning_store]() {
                    if (!alive->load()) {
                        return;
                    }
                    // 上一个工作线程已结束，join 后才允许启动新实验。
                    if (experiment_thread->joinable()) {
                        experiment_thread->join();
                    }
                    elapsed_timer->disconnect();
                    *running_flag = false;
                    result_buffer->set_text(result);
                    if (learning_store) {
                        try {
                            learning_store->record_run(
                                function_id,
                                raw_output,
                                duration_ms,
                                source_snapshot,
                                git_state.commit,
                                git_state.dirty);
                        } catch (const exception& error) {
                            cerr << "Failed to record run for " << function_id
                                 << ": " << error.what() << endl;
                        }
                    }
                    if (experiment_spinner) {
                        experiment_spinner->set_spinning(false);
                        experiment_spinner->set_visible(false);
                    }
                    if (experiment_status_label) {
                        experiment_status_label->set_visible(false);
                    }
                });
        });
}

void MainWindow::populate_topic_list(
    const string& category_name,
    const ChapterMeta& chapter,
    GtkSourceView* source_view,
    Gtk::TextView* result_view,
    Gtk::ListBox& topics_list,
    Gtk::Label* knowledge_description_label,
    Gtk::Spinner* experiment_spinner,
    Gtk::Label* experiment_status_label,
    Gtk::Label* header_title_label,
    Gtk::Label* header_description_label,
    Gtk::Image* header_icon,
    Gtk::TextView* note_view) {
    if (chapter.subchapters.empty()) {
        auto row = Gtk::make_managed<Gtk::ListBoxRow>();
        row->set_selectable(false);
        row->set_activatable(false);

        auto label = Gtk::make_managed<Gtk::Label>("知识点框架待补充");
        label->set_halign(Gtk::Align::START);
        label->add_css_class("dim-label");
        label->set_margin_top(12);
        label->set_margin_bottom(12);
        label->set_margin_start(12);
        label->set_margin_end(12);
        row->set_child(*label);
        topics_list.append(*row);

        if (knowledge_description_label) {
            knowledge_description_label->set_text(chapter.description);
        }
        return;
    }

    auto selection_by_row =
        make_shared<std::map<Gtk::ListBoxRow*, TopicSelection>>();
    auto current_topic = make_shared<TopicSelection>();
    const auto note_buffer =
        note_view ? note_view->get_buffer() : Glib::RefPtr<Gtk::TextBuffer> {};
    auto note_loading = make_shared<bool>(false);
    auto note_dirty = make_shared<bool>(false);
    auto note_timer = make_shared<sigc::connection>();

    // 笔记自动保存：编辑停止 600ms 后写入；切换知识点前先落盘。
    auto flush_note = make_shared<function<void()>>();
    *flush_note = [this, current_topic, note_buffer, note_dirty]() {
        if (!*note_dirty || !note_buffer || !m_learning_store
            || current_topic->function_id.empty()) {
            return;
        }
        try {
            const auto progress =
                m_learning_store->load_progress(current_topic->function_id);
            m_learning_store->save_progress(
                current_topic->function_id,
                progress.mastery,
                string(note_buffer->get_text().raw()));
        } catch (const exception& error) {
            cerr << "Failed to save note for " << current_topic->function_id
                 << ": " << error.what() << endl;
        }
        *note_dirty = false;
    };
    if (note_buffer) {
        note_buffer->signal_changed().connect(
            [note_loading, note_dirty, note_timer, flush_note]() {
                if (*note_loading) {
                    return;
                }
                *note_dirty = true;
                if (note_timer->connected()) {
                    note_timer->disconnect();
                }
                *note_timer = Glib::signal_timeout().connect(
                    [flush_note]() {
                        (*flush_note)();
                        return false;
                    },
                    600);
            });
    }

    // 激活只负责高亮、头部、说明、笔记加载和源码显示；
    // 运行由运行按钮显式触发，条目本身（标题与描述）不响应点击。
    auto activate_topic = make_shared<function<void(Gtk::ListBoxRow*)>>(
        [this,
         selection_by_row,
         current_topic,
         knowledge_description_label,
         source_view,
         header_title_label,
         header_description_label,
         header_icon,
         note_view,
         note_buffer,
         note_loading,
         flush_note](Gtk::ListBoxRow* row) {
            const auto found = selection_by_row->find(row);
            if (found == selection_by_row->end()) {
                return;
            }

            for (const auto& entry : *selection_by_row) {
                entry.first->remove_css_class("topic-active");
            }
            row->add_css_class("topic-active");

            if (knowledge_description_label) {
                knowledge_description_label->set_text(
                    found->second.description);
            }
            // 章节头部横条随激活的知识点切换为该知识点的标题与描述。
            if (header_title_label) {
                header_title_label->set_text(found->second.title);
            }
            if (header_description_label) {
                header_description_label->set_text(found->second.description);
            }
            if (header_icon) {
                configure_image(*header_icon, found->second.icon, 36);
            }

            (*flush_note)();
            *current_topic = found->second;
            if (note_view && note_buffer) {
                note_view->set_sensitive(true);
                *note_loading = true;
                note_buffer->set_text(
                    m_learning_store
                        ? m_learning_store
                              ->load_progress(found->second.function_id)
                              .note
                        : "");
                *note_loading = false;
            }

            display_source(
                source_view,
                m_content_loader,
                found->second.source_path,
                found->second.member_name);
        });

    string current_group;
    for (const auto& subchapter : chapter.subchapters) {
        if (!subchapter.group.empty() && subchapter.group != current_group) {
            current_group = subchapter.group;
            if (const auto* group = find_group(chapter, current_group)) {
                auto header = Gtk::make_managed<Gtk::ListBoxRow>();
                header->set_selectable(false);
                header->set_activatable(false);
                header->add_css_class("topic-group");

                auto header_box = Gtk::make_managed<Gtk::Box>(
                    Gtk::Orientation::HORIZONTAL,
                    10);
                header_box->set_margin_top(12);
                header_box->set_margin_bottom(4);
                header_box->append(*create_icon(group->icon, 18));

                auto text_box = Gtk::make_managed<Gtk::Box>(
                    Gtk::Orientation::VERTICAL,
                    2);
                text_box->set_hexpand(true);

                auto group_title = Gtk::make_managed<Gtk::Label>(group->title);
                group_title->set_halign(Gtk::Align::START);
                group_title->add_css_class("heading");
                text_box->append(*group_title);

                auto group_description =
                    Gtk::make_managed<Gtk::Label>(group->description);
                group_description->set_halign(Gtk::Align::START);
                group_description->set_xalign(0);
                group_description->set_wrap(true);
                group_description->add_css_class("dim-label");
                text_box->append(*group_description);

                header_box->append(*text_box);
                header->set_child(*header_box);
                topics_list.append(*header);
            }
        }

        auto row = Gtk::make_managed<Gtk::ListBoxRow>();
        row->set_selectable(false);
        row->set_activatable(false);
        row->add_css_class("topic-row");

        const string function_id = make_function_id(
            category_name,
            chapter.name,
            subchapter.name);
        (*selection_by_row)[row] = {
            .description = subchapter.description,
            .source_path = resolve_source_path(chapter, subchapter),
            .member_name = subchapter.name,
            .title = subchapter.title,
            .function_id = function_id,
            .icon = subchapter.icon,
        };

        auto row_box = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL,
            12);
        row_box->append(*create_icon(subchapter.icon, 20));

        auto text_box = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::VERTICAL,
            4);
        text_box->set_hexpand(true);

        static const vector<string> importance_levels = {
            "未评", "简单", "一般", "正常", "复杂", "极难"};

        auto title_row = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 8);

        auto point_title = Gtk::make_managed<Gtk::Label>(subchapter.title);
        point_title->set_halign(Gtk::Align::START);
        point_title->add_css_class("heading");
        title_row->append(*point_title);

        // 重要度：内容作者基于教学与工程实践给出的客观难度判断，只读展示，
        // 用户不可修改；未标注时不显示，避免给未评估内容造成虚假精确感。
        // 文字徽章 + 星级并列展示，五个等级各用一种颜色区分。
        const int importance = clamp(subchapter.importance, 0, 5);
        if (importance > 0) {
            const string level_text = importance_levels[static_cast<size_t>(importance)];
            const string level_class = "importance-level-" + to_string(importance);
            const string tooltip =
                "内容难度：" + level_text + "（由内容作者标注，只读）";

            auto importance_group = Gtk::make_managed<Gtk::Box>(
                Gtk::Orientation::HORIZONTAL, 4);
            importance_group->set_valign(Gtk::Align::CENTER);
            importance_group->set_tooltip_text(tooltip);

            auto importance_badge = Gtk::make_managed<Gtk::Label>(level_text);
            importance_badge->add_css_class("badge");
            importance_badge->add_css_class("badge-importance");
            importance_badge->add_css_class(level_class);
            importance_group->append(*importance_badge);

            auto importance_stars = Gtk::make_managed<Gtk::Box>(
                Gtk::Orientation::HORIZONTAL, 6);
            importance_stars->add_css_class("importance-stars");
            importance_stars->add_css_class(level_class);
            for (int star_index = 1; star_index <= 5; ++star_index) {
                auto icon = Gtk::make_managed<Gtk::Image>();
                icon->set_from_icon_name(
                    star_index <= importance
                        ? "starred-symbolic"
                        : "non-starred-symbolic");
                icon->set_pixel_size(14);
                importance_stars->append(*icon);
            }
            importance_group->append(*importance_stars);

            title_row->append(*importance_group);
        }
        text_box->append(*title_row);

        auto point_description =
            Gtk::make_managed<Gtk::Label>(subchapter.description);
        point_description->set_halign(Gtk::Align::START);
        point_description->set_xalign(0);
        point_description->set_wrap(true);
        point_description->add_css_class("dim-label");
        text_box->append(*point_description);
        row_box->append(*text_box);

        // 操作区：运行、历史、复制集中在一个 Box 中，与条目文字以分隔线隔离。
        const TopicSelection topic = (*selection_by_row)[row];
        auto actions = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 6);
        actions->set_valign(Gtk::Align::CENTER);
        actions->add_css_class("topic-actions");

        auto run = Gtk::make_managed<Gtk::Button>("运行");
        run->add_css_class("suggested-action");
        run->add_css_class("btn-primary");
        run->add_css_class("btn-sm");
        run->add_css_class("topic-run");
        const bool can_run =
            m_function_registry.contains(topic.function_id);
        run->set_sensitive(can_run);
        run->set_tooltip_text(can_run
            ? "运行该知识点的实验代码"
            : "该知识点尚未实现可运行实验");
        if (can_run && result_view) {
            run->signal_clicked().connect(
                [this,
                 row,
                 activate_topic,
                 topic,
                 result_view,
                 experiment_spinner,
                 experiment_status_label]() {
                    (*activate_topic)(row);
                    start_experiment(
                        topic.function_id,
                        topic.source_path,
                        topic.member_name,
                        *result_view,
                        experiment_spinner,
                        experiment_status_label);
                });
        }
        actions->append(*run);

        // 历史与解释依赖具体知识点，各自绑定当前这一条 topic，不再共用
        // 一对随“当前激活知识点”切换的按钮；点击时先激活本行（高亮、
        // 头部、笔记与源码随之切换），再执行对应动作。
        auto history_button = Gtk::make_managed<Gtk::Button>("运行历史");
        history_button->add_css_class("btn-sm");
        history_button->set_tooltip_text("查看该知识点的运行记录");
        history_button->signal_clicked().connect(
            [this, row, activate_topic, topic]() {
                (*activate_topic)(row);
                show_history_dialog(
                    topic.function_id,
                    topic.source_path,
                    topic.member_name,
                    topic.title);
            });
        actions->append(*history_button);

        auto explain_button = Gtk::make_managed<Gtk::Button>("AI 讲解");
        explain_button->add_css_class("btn-sm");
        explain_button->set_tooltip_text(
            "把该知识点的说明与源码组成解释请求放入剪贴板，并唤起本机 AI 助手");
        explain_button->signal_clicked().connect(
            [this, row, activate_topic, topic]() {
                (*activate_topic)(row);
                explain_with_local_ai(
                    m_content_loader,
                    topic.title,
                    topic.description,
                    topic.source_path,
                    topic.member_name);
            });
        actions->append(*explain_button);

        // 熟练度：用户自评的五星评分，自由打分并持久化；到 5 星后运行
        // 按钮置灰，降低星级即可恢复运行。重要度不在这里——它是只读的
        // 客观难度标注，显示在条目标题旁，见上方 title_row。
        KnowledgeProgress saved_progress;
        if (m_learning_store) {
            try {
                saved_progress = m_learning_store->load_progress(function_id);
            } catch (const exception& error) {
                cerr << "Failed to load progress for " << function_id << ": "
                     << error.what() << endl;
            }
        }
        auto mastery = make_shared<int>(clamp(saved_progress.mastery, 0, 5));

        auto persist_rating = [this, function_id, mastery]() {
            if (!m_learning_store) {
                return;
            }
            try {
                const auto note =
                    m_learning_store->load_progress(function_id).note;
                m_learning_store->save_progress(function_id, *mastery, note);
            } catch (const exception& error) {
                cerr << "Failed to save rating for " << function_id << ": "
                     << error.what() << endl;
            }
        };
        auto apply_run_state = [run, can_run, mastery]() {
            if (!can_run) {
                return;
            }
            const bool finished = *mastery >= 5;
            run->set_sensitive(!finished);
            run->set_tooltip_text(finished
                ? "已完全掌握；如需重跑请先降低熟练度"
                : "运行该知识点的实验代码");
        };
        // 熟练度五星评分行：点击第 n 颗设为 n 星，再点当前星降一星；
        // 星星右侧跟随文字标识，随当前星级显示对应含义，悬浮单颗星
        // 也带同样的含义说明。
        auto make_star_row = [persist_rating, apply_run_state](
                                  const vector<string>& level_labels,
                                  const shared_ptr<int>& value) {
            auto row = Gtk::make_managed<Gtk::Box>(
                Gtk::Orientation::HORIZONTAL, 6);
            row->add_css_class("star-row");
            row->add_css_class("star-row-mastery");

            auto level_label = Gtk::make_managed<Gtk::Label>();
            level_label->add_css_class("star-level-label");
            level_label->set_halign(Gtk::Align::START);

            auto star_buttons = make_shared<vector<Gtk::Button*>>();
            auto refresh = make_shared<function<void()>>();
            *refresh = [star_buttons, value, level_label, level_labels]() {
                for (size_t index = 0; index < star_buttons->size(); ++index) {
                    if (auto* icon = dynamic_cast<Gtk::Image*>(
                            (*star_buttons)[index]->get_child())) {
                        icon->set_from_icon_name(
                            static_cast<int>(index) < *value
                                ? "starred-symbolic"
                                : "non-starred-symbolic");
                    }
                }
                const size_t level =
                    static_cast<size_t>(clamp(*value, 0, 5));
                level_label->set_text(level_labels[level]);
            };
            for (int star_index = 1; star_index <= 5; ++star_index) {
                auto star = Gtk::make_managed<Gtk::Button>();
                star->add_css_class("flat");
                star->add_css_class("star-button");
                star->set_tooltip_text(level_labels[static_cast<size_t>(star_index)]);
                auto icon = Gtk::make_managed<Gtk::Image>();
                icon->set_pixel_size(14);
                star->set_child(*icon);
                star->signal_clicked().connect(
                    [value, star_index, refresh, persist_rating, apply_run_state]() {
                        *value = (*value == star_index)
                            ? star_index - 1
                            : star_index;
                        (*refresh)();
                        persist_rating();
                        apply_run_state();
                    });
                star_buttons->push_back(star);
                row->append(*star);
            }
            row->append(*level_label);
            (*refresh)();
            return row;
        };

        static const vector<string> mastery_levels = {
            "未学", "了解", "理解", "掌握", "熟练", "精通"};

        actions->append(*make_star_row(mastery_levels, mastery));
        apply_run_state();

        row_box->append(*actions);

        row->set_child(*row_box);
        topics_list.append(*row);
    }
}

Glib::RefPtr<Gtk::Builder> MainWindow::get_chapter_builder(
    const string& category_name,
    const string& chapter_name) {
    const string key = chapter_key(category_name, chapter_name);
    if (auto cached = m_chapter_builders.find(key);
        cached != m_chapter_builders.end()) {
        return cached->second;
    }

    const auto* chapter = m_catalog.find_chapter(category_name, chapter_name);
    if (!chapter) {
        cerr << "Chapter not found: " << key << endl;
        return {};
    }

    auto builder = Gtk::Builder::create_from_resource(chapter->resource_path);
    m_chapter_builders[key] = builder;
    return builder;
}
