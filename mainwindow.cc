#include "mainwindow.h"
#include "app_icon.h"
#include "content/source_locator.h"
#include "render/markdown_renderer.h"
#include "services/ai_service.h"
#include "ui/progress_page.h"

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

// AI 服务商 Key 在 LearningStore.app_settings 里的存储键；应用内设置面板
// 写入，四处需要 Key 的地方统一从这里读，不再各自散落地读环境变量。
const char* kSettingArkApiKey = "ai_provider_key_ark";
const char* kSettingDeepseekApiKey = "ai_provider_key_deepseek";

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

// 在对话框内容区底部居中放一行按钮；不加"关闭"——系统对话框本身自带
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

// 讲解类提示词（讲解/自测/理论文档/讲解差异）共用的风格提示：贴近主流
// 中文 C++ 教程的讲法和术语习惯，不生造术语。这里不是真的联网抓取这些
// 站点内容——AiService 没有搜索/浏览能力，只是提示模型
// 往这个方向组织语言，权当术语和讲法的锚点。
const char* kChineseTutorialStyleHint =
    "讲解风格和术语尽量贴近菜鸟教程、C语言中文网、微软 Learn 中文文档、"
    "w3cschool 这类主流中文 C++ 教程的习惯讲法，不要生造术语。";

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

// 欢迎页的 Blueprint 根控件名；学习进度标签页插在它后面。
constexpr const char* kWelcomePageWidget = "welcome_page";

// 学习进度页固定的 Stack 子页面名。跟 kHandbookPageKey 一样用双下划线
// 包起来，不会跟真实章节 ID（都是 ASCII 标识符拼接）冲突。
constexpr const char* kProgressPageKey = "__progress__";

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
    auto settings_button =
        m_main_builder->get_widget<Gtk::Button>("settings_button");

    if (!m_category_sidebar || !m_chapter_stack || !m_chapter_tab_box
        || !settings_button) {
        throw runtime_error("Failed to get required widgets from main UI");
    }
    settings_button->signal_clicked().connect(
        sigc::mem_fun(*this, &MainWindow::show_settings_dialog));

    load_chapter_metadata();
    // 学习存储必须在建侧边栏之前打开：setup_category_sidebar() 里第一个
    // 分类按钮的 set_active() 会立刻触发 build_chapter_tabs()，进而构建
    // 学习进度页并读取熟练度。放在后面的话首屏统计恒为全 0，要切一次
    // 分类再切回来才对——这是曾经出现过的真实症状。
    open_learning_store();
    setup_category_sidebar();
}

void MainWindow::load_chapter_metadata() {
    const string source =
        m_content_loader.load_resource("/app/data/chapter_catalog.json");
    if (source.empty()) {
        throw runtime_error("generated chapter Catalog not found in GResource");
    }
    m_catalog = ChapterCatalog::from_runtime_json(source);
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
    // 侧边栏只有分类按钮。手册和学习进度都不在这里：它们是分类内部的
    // 合成标签页，见 build_chapter_tabs()——手册按分类各自独立，没有
    // 跨分类的全局入口。
    Gtk::ToggleButton* group_owner = nullptr;
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

        if (group_owner) {
            button->set_group(*group_owner);
        } else {
            group_owner = button;
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
    // 按钮随上面的 remove 一起销毁，记录的指针必须同时作废。
    m_handbook_tab_buttons.clear();

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

    // 没有欢迎页的分类（数据结构与算法、设计模式）把手册排在最前面；
    // 有欢迎页的分类则排在欢迎页和学习进度之后，见下面的循环。
    const bool has_welcome_page = any_of(
        category->second.begin(),
        category->second.end(),
        [](const ChapterMeta& chapter) {
            return chapter.widget_name == kWelcomePageWidget;
        });
    if (!has_welcome_page) {
        append_handbook_tab(category_name);
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

        // 学习进度和手册紧跟在欢迎页后面。欢迎页只有 cpp 分类有，靠根
        // 控件名识别（跟本文件里判断 code 页面用 "chapter_page" 是同一个
        // 惯例），不硬编码章节 name。
        if (chapter.widget_name == kWelcomePageWidget) {
            append_progress_tab();
            append_handbook_tab(category_name);
        }
    }

    if (!m_tab_buttons.empty()) {
        m_tab_buttons.front()->set_active(true);
    }
}

// 学习进度是合成标签页：数据来自 LearningStore 与 ChapterCatalog 的交叉
// 聚合，不对应 athena.json 里的任何章节，因此不走 ensure_chapter_page()
// 那套 builder 缓存，每次都直接构建控件树。页面名登记进
// m_active_page_names，切到别的分类时和普通章节页一起被移除，切回来重新
// 构建，星级变化因此总是最新的。
void MainWindow::append_progress_tab() {
    std::map<string, int> mastery_by_id;
    if (m_learning_store) {
        try {
            mastery_by_id = m_learning_store->load_all_mastery();
        } catch (const exception& error) {
            cerr << "Failed to load mastery stats: " << error.what() << endl;
        }
    }
    const CategoryProgress progress =
        aggregate_category_progress(m_catalog, "cpp", mastery_by_id);
    m_chapter_stack->add(
        *make_progress_page("C++", progress), kProgressPageKey, "学习进度");
    m_active_page_names.insert(kProgressPageKey);

    auto tab_button = Gtk::make_managed<Gtk::ToggleButton>();
    tab_button->add_css_class("pill");
    tab_button->add_css_class("chapter-tab");
    tab_button->set_tooltip_text("各章节知识点的掌握情况统计");

    auto tab_content = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
    tab_content->append(*create_icon(
        {.type = "theme", .name = "utilities-system-monitor-symbolic"}, 16));
    tab_content->append(*Gtk::make_managed<Gtk::Label>("学习进度"));
    tab_button->set_child(*tab_content);

    if (!m_tab_buttons.empty()) {
        tab_button->set_group(*m_tab_buttons.front());
    }

    tab_button->signal_toggled().connect([this, tab_button]() {
        if (!tab_button->get_active()) {
            return;
        }
        if (auto* child = m_chapter_stack->get_child_by_name(kProgressPageKey)) {
            m_chapter_stack->set_visible_child(*child);
        }
        m_current_chapter = kProgressPageKey;
    });

    m_chapter_tab_box->append(*tab_button);
    m_tab_buttons.push_back(tab_button);
}

// 手册也是合成标签页，但页面本身懒构建且常驻 Stack（原因见
// ensure_handbook_page）；这里每次重建的只是标签按钮。按钮指针按分类记
// 下来，"本章总纲"跳转时要靠它同步标签栏的选中态。
void MainWindow::append_handbook_tab(const string& category_name) {
    auto tab_button = Gtk::make_managed<Gtk::ToggleButton>();
    tab_button->add_css_class("pill");
    tab_button->add_css_class("chapter-tab");
    tab_button->set_tooltip_text("本分类的手册：理论、原则与工程思想");

    auto tab_content = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
    tab_content->append(*create_icon(
        {.type = "theme", .name = "accessories-dictionary-symbolic"}, 16));
    tab_content->append(*Gtk::make_managed<Gtk::Label>("手册"));
    tab_button->set_child(*tab_content);

    if (!m_tab_buttons.empty()) {
        tab_button->set_group(*m_tab_buttons.front());
    }

    tab_button->signal_toggled().connect(
        [this, tab_button, category_name]() {
            if (!tab_button->get_active()) {
                return;
            }
            show_handbook_page(category_name);
        });

    m_chapter_tab_box->append(*tab_button);
    m_tab_buttons.push_back(tab_button);
    m_handbook_tab_buttons[category_name] = tab_button;
}

// 手册页面的 Stack 子页面名：每个分类一部手册，各自一个页面。分类名是
// ASCII 标识符，加上双下划线后缀不会跟真实章节 ID 冲突。
string handbook_page_key(const string& category_name) {
    return category_name + ".__handbook__";
}

// 手册页面**不登记进 m_active_page_names**：它由 make_managed 直接建出，
// 没有 builder 持有引用，一旦从 Stack 移除控件就会析构，而
// m_article_views 里的 ArticleView 还指着里面的宿主控件。所以切分类时把
// 它留在 Stack 里（只是没有标签按钮指向它），每个分类最多留一页，
// WKWebView 常驻——这也正是 ADR 0012 选常驻页面而非临时 Dialog 的理由。
void MainWindow::ensure_handbook_page(const string& category_name) {
    if (m_handbook_built_categories.count(category_name) > 0) {
        return;
    }
    // 即使渲染失败也标记为已构建，跟其它章节页面初始化失败时的处理一致，
    // 不重复尝试。
    m_handbook_built_categories.insert(category_name);

    const string page_key = handbook_page_key(category_name);
    const auto& documents = m_catalog.handbook_documents(category_name);

    // 还没收录文档的分类（当前是数据结构与算法、设计模式）也给一个手册
    // 标签页，但用一句占位说明代替 WebView：既不谎称有内容，也不为空文档
    // 白起一个 WKWebView。
    if (documents.empty()) {
        auto placeholder = Gtk::make_managed<Gtk::Label>(
            "本分类的手册还没有收录文档。");
        placeholder->set_halign(Gtk::Align::CENTER);
        placeholder->set_valign(Gtk::Align::CENTER);
        placeholder->add_css_class("dim-label");
        m_chapter_stack->add(*placeholder, page_key, "手册");
        return;
    }

    auto page = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL);
    page->set_hexpand(true);
    page->set_vexpand(true);
    page->set_margin_top(16);
    page->set_margin_start(20);
    page->set_margin_end(20);
    page->set_margin_bottom(20);
    page->add_css_class("article-page");

    auto frame = Gtk::make_managed<Gtk::Frame>();
    frame->set_hexpand(true);
    frame->set_vexpand(true);
    frame->add_css_class("article-surface");

    auto host = Gtk::make_managed<Gtk::DrawingArea>();
    host->set_hexpand(true);
    host->set_vexpand(true);
    frame->set_child(*host);
    page->append(*frame);

    m_chapter_stack->add(*page, page_key, "手册");

    // 一部手册是该分类下各份静态文档的合集：按本分类的
    // handbook_documents 顺序拼接，一次性喂给标题解析/渲染函数，生成
    // 一份跨文档的完整目录；每份文档自己的标题数量决定它在合集里的
    // 起始锚点（athena-heading-N，N 是它前面所有文档的标题总数），
    // “本章总纲”按钮据此跳到对应位置，不用整份手册单独存一份。
    auto& anchor_by_document = m_handbook_anchors_by_category[category_name];
    string combined_markdown;
    size_t heading_count = 0;
    for (const auto& document : documents) {
        const string markdown = m_content_loader.load_document(document);
        if (markdown.empty()) {
            cerr << "Failed to load handbook document: " << document << endl;
            continue;
        }
        vector<MarkdownHeading> headings;
        try {
            headings = parse_markdown_headings(markdown);
        } catch (const exception& error) {
            cerr << "Failed to parse handbook document " << document
                 << ": " << error.what() << endl;
            continue;
        }
        if (!headings.empty()) {
            anchor_by_document[document] =
                "athena-heading-" + to_string(heading_count);
        }
        heading_count += headings.size();

        if (!combined_markdown.empty()) {
            combined_markdown += "\n\n---\n\n";
        }
        combined_markdown += markdown;
    }

    if (combined_markdown.empty()) {
        cerr << "Handbook has no renderable content" << endl;
        return;
    }

    try {
        const auto headings = parse_markdown_headings(combined_markdown);
        const string stylesheet =
            m_content_loader.load_resource("/app/article.css");
        if (stylesheet.empty()) {
            throw runtime_error("Article stylesheet is unavailable");
        }

        auto view = create_platform_article_view(*host, *this);
        if (!view) {
            throw runtime_error("No WebView backend is available");
        }
        // 手册文档目前都在同一个目录下，用第一份文档的目录作为相对资源
        // （图片等）的基准路径。
        view->load_html(
            render_markdown_html(combined_markdown, stylesheet, headings),
            m_content_loader.document_base_directory(documents.front()));
        m_article_views[page_key] = std::move(view);
    } catch (const exception& error) {
        cerr << "Failed to render handbook for " << category_name << ": "
             << error.what() << endl;
    }
}

// 切到某个分类的手册标签页（懒构建，每个分类只建一次）；
// jump_to_document 非空时跳到该文档在本分类手册里的起始标题——用于章节
// 的“本章总纲”按钮，文档必须已经在本分类的 handbook_documents 里（生成器
// check 时校验），否则跳转是 no-op。
void MainWindow::show_handbook_page(
    const string& category_name,
    const string& jump_to_document) {
    ensure_handbook_page(category_name);

    const string page_key = handbook_page_key(category_name);
    if (auto* child = m_chapter_stack->get_child_by_name(page_key)) {
        m_chapter_stack->set_visible_child(*child);
    }
    // 手册是本分类标签行里的一个标签页，切过去要让对应按钮跟着选中，
    // 否则标签栏的高亮和实际显示的页面对不上。
    if (auto* button = m_handbook_tab_buttons[category_name]) {
        if (!button->get_active()) {
            button->set_active(true);
        }
    }
    m_current_chapter = page_key;

    if (jump_to_document.empty()) {
        return;
    }
    const auto anchors = m_handbook_anchors_by_category.find(category_name);
    if (anchors == m_handbook_anchors_by_category.end()) {
        return;
    }
    const auto anchor = anchors->second.find(jump_to_document);
    if (anchor == anchors->second.end()) {
        return;
    }
    const auto view = m_article_views.find(page_key);
    if (view != m_article_views.end() && view->second) {
        view->second->scroll_to_anchor(anchor->second);
    }
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
    auto chapter_overview_button =
        builder->get_widget<Gtk::Button>("chapter_overview_button");

    // 章节总纲不依赖当前选中的知识点，常驻可点，独立于知识点列表接线。
    // 有 overview_document 时跳到**本分类**手册页面里对应位置（人工撰写
    // 的静态文档，不联网、不调用 AI）；没有时退回复制提示词到剪贴板并
    // 唤起本机 AI 助手。
    if (chapter_overview_button) {
        chapter_overview_button->signal_clicked().connect(
            [this,
             category_name,
             title = chapter.title,
             description = chapter.description,
             subchapters = chapter.subchapters,
             overview_document = chapter.overview_document]() {
                if (!overview_document.empty()) {
                    show_handbook_page(category_name, overview_document);
                } else {
                    explain_chapter_overview_with_local_ai(
                        title, description, subchapters);
                }
            });
    }

    if (topics_list) {
        populate_topic_list(
            chapter,
            source_view,
            result_view,
            *topics_list,
            knowledge_description_label,
            experiment_spinner,
            experiment_status_label,
            title_label,
            description_label,
            chapter_icon);
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

string MainWindow::resolve_ai_api_key(
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
// resolve_ai_api_key()，不缓存。
void MainWindow::show_settings_dialog() {
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
        resolve_ai_api_key(kSettingArkApiKey, "ATHENA_ARK_API_KEY"));
    auto* deepseek_entry = add_key_row(
        "DeepSeek（ATHENA_DEEPSEEK_API_KEY）",
        resolve_ai_api_key(kSettingDeepseekApiKey, "ATHENA_DEEPSEEK_API_KEY"));

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

    lock_for_modal_dialog(*this, *dialog);
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
        resolve_ai_api_key(kSettingArkApiKey, "ATHENA_ARK_API_KEY");
    const string deepseek_api_key =
        resolve_ai_api_key(kSettingDeepseekApiKey, "ATHENA_DEEPSEEK_API_KEY");
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
                    show_ai_response_dialog(
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
    lock_for_modal_dialog(*this, *dialog);
}

// 打开对话框，异步用给定提示词调用 AI（优先火山方舟豆包，失败或未配置
// 再退回 DeepSeek），结果当 Markdown 解析后用跟手册页面一样的排版显示：md4c
// 转 HTML、WKWebView（macOS）渲染，代码块、标题、列表都有正常版式，
// 不是纯文本 TextView 堆一坨——AI 的回答经常代码和说明夹杂，纯文本对
// 代码不友好。网络请求在独立线程执行，HTML 只在主线程构造和加载；
// article_view 在对话框隐藏时显式 reset，跟对话框同生命周期。运行历史
// 的“AI 讲解差异”用这个对话框。
void MainWindow::show_ai_markdown_dialog(
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
    lock_for_modal_dialog(*this, *dialog);

    // 只在这几个 AI 对话框里把正文字号调大，不改 resources/article.css
    // 本身——真正的 article 章节阅读页面用原来的 19px，不受影响。
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

void MainWindow::show_ai_response_dialog(
    const string& dialog_title,
    const string& prompt,
    const string& ark_api_key,
    const string& deepseek_api_key) {
    show_ai_markdown_dialog(
        dialog_title, prompt, ark_api_key, deepseek_api_key,
        "正在请求 AI，请稍候…", 760, 620);
}

// 打开对话框，异步向 AI（优先火山方舟豆包，失败或未配置再退回 DeepSeek）请求
// 针对该知识点具体源码的选择题（JSON 格式，每题含题干、选项、正确选项
// 下标和解释），逐题展示；每题先选一个选项，点“提交答案”才判对错、给
// 解释，颜色区分对错。返回的 JSON 解析失败时退化为纯文本展示，不崩溃、
// 不隐藏结果。
void MainWindow::show_ai_quiz_dialog(
    const string& function_id,
    const string& topic_title,
    const string& description,
    const string& source_path,
    const string& member_name,
    const string& ark_api_key,
    const string& deepseek_api_key,
    function<bool(int)> on_mastery_changed) {
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
        " 不要输出 JSON 之外的任何文字。\n\n知识点说明：" + description;
    const auto body = member_source_body(m_content_loader, source_path, member_name);
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
    lock_for_modal_dialog(*this, *dialog);

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
    const ChapterMeta& chapter,
    GtkSourceView* source_view,
    Gtk::TextView* result_view,
    Gtk::ListBox& topics_list,
    Gtk::Label* knowledge_description_label,
    Gtk::Spinner* experiment_spinner,
    Gtk::Label* experiment_status_label,
    Gtk::Label* header_title_label,
    Gtk::Label* header_description_label,
    Gtk::Image* header_icon) {
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

    // 激活只负责高亮、头部、说明和源码显示；
    // 运行由运行按钮显式触发，条目本身（标题与描述）不响应点击。
    auto activate_topic = make_shared<function<void(Gtk::ListBoxRow*)>>(
        [this,
         selection_by_row,
         knowledge_description_label,
         source_view,
         header_title_label,
         header_description_label,
         header_icon](Gtk::ListBoxRow* row) {
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

        const string& function_id = subchapter.function_id;
        (*selection_by_row)[row] = {
            .description = subchapter.description,
            .source_path = subchapter.source,
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
        // 头部与源码随之切换），再执行对应动作。
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

        // 熟练度是最近一次完整 AI 自测的量化结果，只读展示。重要度不在
        // 这里——它是内容作者给出的客观难度标注，见上方 title_row。
        int saved_mastery = 0;
        if (m_learning_store) {
            try {
                saved_mastery = m_learning_store->load_mastery(function_id);
            } catch (const exception& error) {
                cerr << "Failed to load progress for " << function_id << ": "
                     << error.what() << endl;
            }
        }
        auto mastery = make_shared<int>(clamp(saved_mastery, 0, 5));

        auto mastery_row = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 4);
        mastery_row->add_css_class("star-row");
        mastery_row->add_css_class("star-row-mastery");
        mastery_row->set_tooltip_text(
            "熟练度由最近一次完成的 AI 自测成绩自动评定，不能手动修改");
        auto mastery_caption = Gtk::make_managed<Gtk::Label>("熟练度");
        mastery_caption->add_css_class("star-caption");
        mastery_row->append(*mastery_caption);

        auto mastery_stars = make_shared<vector<Gtk::Image*>>();
        for (int index = 0; index < 5; ++index) {
            auto star = Gtk::make_managed<Gtk::Image>();
            star->set_pixel_size(14);
            mastery_stars->push_back(star);
            mastery_row->append(*star);
        }
        auto mastery_label = Gtk::make_managed<Gtk::Label>();
        mastery_label->add_css_class("star-level-label");
        mastery_label->set_halign(Gtk::Align::START);
        mastery_row->append(*mastery_label);

        auto refresh_mastery = make_shared<function<void()>>();
        *refresh_mastery = [mastery, mastery_stars, mastery_label]() {
            const int level = clamp(*mastery, 0, 5);
            for (size_t index = 0; index < mastery_stars->size(); ++index) {
                (*mastery_stars)[index]->set_from_icon_name(
                    static_cast<int>(index) < level
                        ? "starred-symbolic"
                        : "non-starred-symbolic");
            }
            mastery_label->set_text(to_string(level) + " 星");
        };
        (*refresh_mastery)();

        auto update_mastery =
            [this, function_id, mastery, refresh_mastery](int score) {
                *mastery = clamp(score, 0, 5);
                (*refresh_mastery)();
                if (!m_learning_store) {
                    return false;
                }
                try {
                    m_learning_store->save_mastery(function_id, *mastery);
                    return true;
                } catch (const exception& error) {
                    cerr << "Failed to save quiz score for " << function_id
                         << ": " << error.what() << endl;
                    return false;
                }
            };

        auto quiz_button = Gtk::make_managed<Gtk::Button>("AI 自测");
        quiz_button->add_css_class("btn-sm");
        quiz_button->set_tooltip_text(
            "需要先在侧边栏底部“设置”里配置至少一个 AI 服务商 Key。题目"
            "依据当前知识点说明和真实源码生成；完成全部题目后由本地规则"
            "自动评分并更新熟练度");
        quiz_button->signal_clicked().connect(
            [this, row, activate_topic, topic, update_mastery]() {
                (*activate_topic)(row);
                const string ark_key =
                    resolve_ai_api_key(kSettingArkApiKey, "ATHENA_ARK_API_KEY");
                const string deepseek_key = resolve_ai_api_key(
                    kSettingDeepseekApiKey, "ATHENA_DEEPSEEK_API_KEY");
                if (!ark_key.empty() || !deepseek_key.empty()) {
                    show_ai_quiz_dialog(
                        topic.function_id,
                        topic.title,
                        topic.description,
                        topic.source_path,
                        topic.member_name,
                        ark_key,
                        deepseek_key,
                        update_mastery);
                } else {
                    auto notice = Gtk::make_managed<Gtk::MessageDialog>(
                        *this,
                        "自测功能需要先在侧边栏底部“设置”里配置至少一个 AI "
                        "服务商 Key",
                        false,
                        Gtk::MessageType::INFO,
                        Gtk::ButtonsType::OK,
                        true);
                    notice->signal_response().connect(
                        [notice](int) { notice->hide(); });
                    notice->show();
                }
            });
        actions->append(*quiz_button);
        actions->append(*mastery_row);

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
