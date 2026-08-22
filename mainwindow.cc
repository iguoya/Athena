#include "mainwindow.h"
#include "app_icon.h"
#include "content/source_locator.h"
#include "practice/pocket_cube/pocket_cube.hpp"
#include "practice/pocket_cube/view.h"
#include "render/markdown_renderer.h"
#include "ui/progress_page.h"

#include <gtksourceview/gtksource.h>
#include <algorithm>
#include <chrono>
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

// “应用实践”类章节的状态日志：把一条新状态插到最上面，超过上限就把
// 最旧的（最下面的）丢掉，记录“就绪/运行中/已完成”这类运行时状态的
// 一小段历史，不是只覆盖显示最新一条。
constexpr size_t kPracticeStatusLogLimit = 5;

void append_practice_status(Gtk::Box* log, const string& text) {
    if (!log) {
        return;
    }
    auto entry = Gtk::make_managed<Gtk::Label>(text);
    entry->set_halign(Gtk::Align::START);
    entry->add_css_class("dim-label");
    log->prepend(*entry);

    size_t count = 0;
    for (auto* child = log->get_first_child(); child;
         child = child->get_next_sibling()) {
        ++count;
    }
    while (count > kPracticeStatusLogLimit) {
        if (auto* oldest = log->get_last_child()) {
            log->remove(*oldest);
        }
        --count;
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
    // 通过插入光标的持久 TextMark 滚动。长源码刚替换进 Buffer 时布局尚未
    // 完成，直接传临时 TextIter 偶尔会保留旧的滚动值，导致高亮函数仍在
    // 视口外；TextView 会在布局完成后继续兑现 mark 对应的滚动请求。
    gtk_text_view_scroll_to_mark(
        GTK_TEXT_VIEW(source_view),
        gtk_text_buffer_get_insert(text_buffer),
        0.15,
        true,
        0.0,
        0.20);
}

string chapter_key(const string& category_name, const string& chapter_name) {
    return category_name + "." + chapter_name;
}

// 欢迎页的 Blueprint 根控件名；学习进度标签页插在它后面。
constexpr const char* kWelcomePageWidget = "welcome_page";

// “应用实践”类章节专属布局（practice_cube.blp）的根控件名；跟
// chapter_page/welcome_page 一样按 widget_name 分支识别。
constexpr const char* kPracticeCubePageWidget = "practice_cube_page";

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
    auto about_button =
        m_main_builder->get_widget<Gtk::Button>("about_button");

    if (!m_category_sidebar || !m_chapter_stack || !m_chapter_tab_box
        || !settings_button || !about_button) {
        throw runtime_error("Failed to get required widgets from main UI");
    }

    load_chapter_metadata();
    // 学习存储必须在建侧边栏之前打开：setup_category_sidebar() 里第一个
    // 分类按钮的 set_active() 会立刻触发 build_chapter_tabs()，进而构建
    // 学习进度页并读取熟练度。放在后面的话首屏统计恒为全 0，要切一次
    // 分类再切回来才对——这是曾经出现过的真实症状。
    open_learning_store();
    // 对话框模块拿的是打开之后的存储指针（可能为 nullptr），因此必须排在
    // open_learning_store() 之后、按钮接线之前。
    m_dialogs = make_unique<LearningDialogs>(
        *this, m_content_loader, m_learning_store.get(), m_ui_alive);
    settings_button->signal_clicked().connect(
        [this]() { m_dialogs->show_settings(); });
    about_button->signal_clicked().connect(
        sigc::mem_fun(*this, &MainWindow::show_about_dialog));
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

    if (chapter.widget_name == kPracticeCubePageWidget) {
        initialize_practice_page(chapter, builder);
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

// 学习进度是合成页面：每次创建都从 LearningStore 批量读取最新熟练度，
// 再与 ChapterCatalog 交叉聚合；不走章节 builder 缓存。
Gtk::Widget* MainWindow::create_progress_page() {
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
    return make_progress_page("C++", progress);
}

// 页面名登记进 m_active_page_names，切到别的分类时和普通章节页一起被
// 移除；切回来时重新创建。标签按钮只创建一次，页面内容可独立替换。
void MainWindow::append_progress_tab() {
    m_chapter_stack->add(
        *create_progress_page(), kProgressPageKey, "学习进度");
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
        refresh_progress_page();
        if (auto* child = m_chapter_stack->get_child_by_name(kProgressPageKey)) {
            m_chapter_stack->set_visible_child(*child);
        }
        m_current_chapter = kProgressPageKey;
    });

    m_chapter_tab_box->append(*tab_button);
    m_tab_buttons.push_back(tab_button);
}

void MainWindow::refresh_progress_page() {
    if (!m_chapter_stack
        || m_active_page_names.find(kProgressPageKey)
            == m_active_page_names.end()) {
        return;
    }

    auto* old_page =
        m_chapter_stack->get_child_by_name(kProgressPageKey);
    const bool was_visible =
        old_page && m_chapter_stack->get_visible_child() == old_page;
    if (old_page) {
        m_chapter_stack->remove(*old_page);
    }

    auto* page = create_progress_page();
    m_chapter_stack->add(*page, kProgressPageKey, "学习进度");
    if (was_visible) {
        m_chapter_stack->set_visible_child(*page);
    }
}

// 手册也是合成标签页，但页面本身懒构建且常驻 Stack（原因见
// ensure_handbook_page）；这里每次重建的只是标签按钮。按钮指针按分类记
// 下来，"说明文档"跳转时要靠它同步标签栏的选中态。
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
    // “说明文档”按钮据此跳到对应位置，不用整份手册单独存一份。
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
// 的“说明文档”按钮，文档必须已经在本分类的 handbook_documents 里（生成器
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

// “应用实践”类章节（practice_cube.blp 等）：标题/简介/说明文档、一个
// 源码框和一个“运行”按钮，没有标准教学页那套知识点列表。目前只有
// 唯一一个知识点（2 阶魔方的 turn），直接绑定第一个 subchapter，不走
// populate_topic_list 那套“多知识点列表 + 选中态”逻辑；以后这类章节
// 真的需要多个知识点时再扩展成通用形式。
//
// 不走 start_experiment()/FunctionRegistry 这条标准运行路径：那套机制
// 面向“调用一个无状态的知识点函数、把文本输出记进运行历史”，但这里
// “运行”驱动的是一个有状态的类实例（转一步要接着上一次转完的状态
// 继续转，不是每次都从复原状态重新算），运行历史/学习进度这些统计对
// “点一下看魔方转”这种交互也没有实际意义。页面自己创建并持有一个
// PocketCube 实例，“运行”按钮直接调用它的方法——源码框里显示的就是
// 真正被执行的代码，不是界面里另外藏一份逻辑。
void MainWindow::initialize_practice_page(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder) {
    auto title_label = builder->get_widget<Gtk::Label>("chapter_title_label");
    auto description_label =
        builder->get_widget<Gtk::Label>("chapter_description_label");
    auto chapter_icon = builder->get_widget<Gtk::Image>("chapter_icon");
    auto chapter_overview_button =
        builder->get_widget<Gtk::Button>("chapter_overview_button");
    auto source_view = GTK_SOURCE_VIEW(
        gtk_builder_get_object(builder->gobj(), "practice_source_view"));
    auto run_button = builder->get_widget<Gtk::Button>("practice_run_button");
    auto result_view = builder->get_widget<Gtk::TextView>("practice_result_view");
    auto status_log = builder->get_widget<Gtk::Box>("practice_status_log");
    auto canvas_host = builder->get_widget<Gtk::Box>("practice_cube_canvas_host");
    auto net_host = builder->get_widget<Gtk::Box>("practice_cube_net_host");

    if (title_label) {
        title_label->set_text(chapter.title);
    }
    if (description_label) {
        description_label->set_text(chapter.description);
    }
    if (chapter_icon) {
        configure_image(*chapter_icon, chapter.icon, 36);
    }
    if (result_view) {
        result_view->get_buffer()->set_text("点击“运行”查看结果。");
    }
    if (!chapter.subchapters.empty()) {
        display_source(
            source_view, m_content_loader, chapter.source,
            chapter.subchapters.front().name);
    }
    append_practice_status(status_log, "就绪");

    // 魔方实例：page 生命周期内持有的一份真实状态，“运行”按钮直接调
    // 它的方法，两个视图从它读取最新状态重绘（见 practice/pocket_cube/
    // view.h 的样例接口说明：state_provider 拉模型 + 手动 queue_draw()）。
    auto cube = make_shared<PocketCube>();
    Gtk::Widget* view_3d = nullptr;
    Gtk::Widget* view_net = nullptr;
    if (canvas_host) {
        view_3d = make_cube_3d_view([cube] { return cube->state(); });
        canvas_host->append(*view_3d);
    }
    if (net_host) {
        view_net = make_cube_net_view([cube] { return cube->state(); });
        net_host->append(*view_net);
    }

    // 跟 initialize_code_page 里说明文档按钮的接线完全一致：有
    // overview_document 就跳手册对应位置，没有就退回剪贴板 + 唤起
    // 本机 AI 助手。
    if (chapter_overview_button) {
        chapter_overview_button->signal_clicked().connect(
            [this,
             category_name = chapter.category,
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

    if (run_button && result_view) {
        run_button->signal_clicked().connect(
            [cube, result_view, status_log, view_3d, view_net]() {
                append_practice_status(status_log, "运行中…");
                ostringstream output;
                cube->run(output);
                result_view->get_buffer()->set_text(output.str());
                if (view_3d) {
                    view_3d->queue_draw();
                }
                if (view_net) {
                    view_net->queue_draw();
                }
                append_practice_status(status_log, "已完成");
            });
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

// 关于对话框：内容是静态的，不像运行历史/AI 自测每次点击都要取新数据，
// 因此惰性创建一次、之后一直复用，不走“设置”那几个业务对话框每次
// new + 隐藏后延迟 delete 的模式——那套复杂度是为了防止异步网络回调
// 踩中已经关闭的对话框，这里没有任何异步操作，用不上。
// 必须显式 set_hide_on_close(true)：否则点原生标题栏关闭按钮会直接销毁
// 这个 make_managed 对象，m_about_dialog 就会变成悬空指针。
void MainWindow::show_about_dialog() {
    if (!m_about_dialog) {
        m_about_dialog = Gtk::make_managed<Gtk::AboutDialog>();
        m_about_dialog->set_program_name("Athena");
        m_about_dialog->set_version(ATHENA_VERSION);
        m_about_dialog->set_comments(
            "为快速渐进学习和掌握 C++ 而开发的自用软件平台，突出学练合一："
            "把零散的代码知识点学习整合到统一框架中，方便运行验证和自我修正。");
        m_about_dialog->set_logo_icon_name("cn.athena.icon");
        m_about_dialog->set_copyright("Copyright (c) 2026 tiger");
        // 木兰宽松许可证第二版不在 Gtk::License 的预置枚举里，用 CUSTOM
        // 附上官方建议的简明声明；完整条款见仓库根目录 LICENSE 文件。
        m_about_dialog->set_license_type(Gtk::License::CUSTOM);
        m_about_dialog->set_license(
            "Athena is licensed under Mulan PSL v2.\n"
            "You can use this software according to the terms and "
            "conditions of the Mulan PSL v2.\n"
            "You may obtain a copy of Mulan PSL v2 at:\n"
            "    http://license.coscl.org.cn/MulanPSL2\n\n"
            "THIS SOFTWARE IS PROVIDED ON AN \"AS IS\" BASIS, WITHOUT "
            "WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING "
            "BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT "
            "FOR A PARTICULAR PURPOSE.\n"
            "See the Mulan PSL v2 for more details.");
        m_about_dialog->set_transient_for(*this);
        m_about_dialog->set_modal(true);
        m_about_dialog->set_hide_on_close(true);
        m_about_dialog->signal_hide().connect(
            [this]() { set_sensitive(true); });
    }
    set_sensitive(false);
    m_about_dialog->present();
}

// 在独立工作线程中执行实验：同一时刻只允许一个实验，
// 运行期间新的运行请求被忽略；结果与耗时经主线程回填。
void MainWindow::start_experiment(
    const string& function_id,
    const string& source_path,
    const string& member_name,
    Gtk::TextView& result_view,
    Gtk::Spinner* experiment_spinner,
    Gtk::Label* experiment_status_label,
    function<void()> on_finished) {
    if (m_experiment_running) {
        return;
    }
    m_experiment_running = true;

    const string source_snapshot =
        load_member_source_text(m_content_loader, source_path, member_name)
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
         started,
         on_finished]() {
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
                 learning_store,
                 on_finished]() {
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
                    if (on_finished) {
                        on_finished();
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
                m_dialogs->show_history(
                    {.function_id = topic.function_id,
                     .title = topic.title,
                     .description = topic.description,
                     .source_path = topic.source_path,
                     .member_name = topic.member_name});
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
                    refresh_progress_page();
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
                // 未配置任何 AI 服务商 Key 时由对话框模块自己提示去
                // “设置”里填，窗口这边不重复一遍判断条件。
                m_dialogs->show_quiz(
                    {.function_id = topic.function_id,
                     .title = topic.title,
                     .description = topic.description,
                     .source_path = topic.source_path,
                     .member_name = topic.member_name},
                    update_mastery);
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
