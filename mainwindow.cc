#include "mainwindow.h"
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

// 计算知识点成员函数源码的指纹，用于运行历史中标记“代码是否修改过”。
string member_source_hash(
    const ContentLoader& loader,
    const string& source_path,
    const string& member_name) {
    try {
        const string source = loader.load_project_file(source_path);
        const auto range = locate_cpp_member_function(source, member_name);
        if (!range) {
            return "";
        }
        const string body =
            source.substr(range->begin, range->end - range->begin);
        return to_string(hash<string> {}(body));
    } catch (const exception&) {
        return "";
    }
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

    cout << "MainWindow initialized successfully" << endl;
}

void MainWindow::load_chapter_metadata() {
    const string source = m_content_loader.load_resource("/app/data/athena.json");
    if (source.empty()) {
        throw runtime_error("athena.json not found in GResource");
    }
    m_catalog = ChapterCatalog::from_json(source);
    cout << "Loaded " << m_catalog.categories().size() << " categories and "
         << m_catalog.chapter_count() << " chapters from athena.json" << endl;
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
        auto builder = get_chapter_builder(category_name, chapter.name);
        if (!builder) {
            cerr << "Failed to create builder for " << page_key << endl;
            continue;
        }

        auto widget = builder->get_widget<Gtk::Widget>(chapter.widget_name);
        if (!widget) {
            cerr << "Failed to get root widget '" << chapter.widget_name
                 << "' for " << page_key << endl;
            continue;
        }

        m_chapter_stack->add(*widget, page_key, chapter.title);
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
            [this, page_key, tab_button, widget]() {
                if (tab_button->get_active()) {
                    m_chapter_stack->set_visible_child(*widget);
                    m_current_chapter = page_key;
                }
            });

        m_chapter_tab_box->append(*tab_button);
        m_tab_buttons.push_back(tab_button);

        if (m_loaded_chapters.find(page_key) != m_loaded_chapters.end()) {
            continue;
        }

        const bool uses_article_page = chapter.widget_name == "article_page";
        if (uses_article_page) {
            if (initialize_article_page(page_key, chapter, builder)) {
                m_loaded_chapters.insert(page_key);
            }
            continue;
        }

        const bool uses_code_page = chapter.widget_name == "chapter_page";
        if (!uses_code_page) {
            continue;
        }
        initialize_code_page(category_name, chapter, builder);
        m_loaded_chapters.insert(page_key);
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
    auto run_button = builder->get_widget<Gtk::Button>("run_button");
    auto result_view = builder->get_widget<Gtk::TextView>("result_view");
    auto topics_label = builder->get_widget<Gtk::Label>("topics_label");
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
    if (run_button) {
        run_button->set_visible(false);
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
    auto copy_source_button =
        builder->get_widget<Gtk::Button>("copy_source_button");
    auto copy_result_button =
        builder->get_widget<Gtk::Button>("copy_result_button");
    auto history_button = builder->get_widget<Gtk::Button>("history_button");

    if (copy_source_button && source_view) {
        copy_source_button->signal_clicked().connect([source_view]() {
            auto* buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(source_view));
            GtkTextIter begin;
            GtkTextIter end;
            gtk_text_buffer_get_bounds(buffer, &begin, &end);
            char* text = gtk_text_buffer_get_text(buffer, &begin, &end, false);
            gdk_clipboard_set_text(
                gtk_widget_get_clipboard(GTK_WIDGET(source_view)), text);
            g_free(text);
        });
    }
    if (copy_result_button && result_view) {
        copy_result_button->signal_clicked().connect([result_view]() {
            auto buffer = result_view->get_buffer();
            Gtk::TextIter begin;
            Gtk::TextIter end;
            buffer->get_bounds(begin, end);
            result_view->get_clipboard()->set_text(
                buffer->get_text(begin, end, false));
        });
    }

    if (topics_label && topics_list) {
        populate_topic_list(
            category_name,
            chapter,
            source_view,
            result_view,
            *topics_list,
            knowledge_description_label,
            experiment_spinner,
            experiment_status_label,
            history_button);
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
        cout << "Learning store opened at " << data_dir << endl;
    } catch (const exception& error) {
        cerr << "Learning store unavailable: " << error.what() << endl;
        m_learning_store.reset();
    }
}

void MainWindow::show_note_dialog(
    const string& function_id,
    const string& topic_title) {
    if (!m_learning_store) {
        return;
    }
    auto dialog = Gtk::make_managed<Gtk::Dialog>();
    dialog->set_title("笔记：" + topic_title);
    dialog->set_transient_for(*this);
    dialog->set_modal(true);
    dialog->set_default_size(560, 400);

    auto* content = dialog->get_content_area();
    content->set_spacing(8);
    auto scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    scrolled->set_policy(Gtk::PolicyType::AUTOMATIC, Gtk::PolicyType::AUTOMATIC);
    scrolled->set_hexpand(true);
    scrolled->set_vexpand(true);
    auto view = Gtk::make_managed<Gtk::TextView>();
    view->set_wrap_mode(Gtk::WrapMode::WORD_CHAR);
    view->get_buffer()->set_text(
        m_learning_store->load_progress(function_id).note);
    scrolled->set_child(*view);
    content->append(*scrolled);

    dialog->add_button("保存", static_cast<int>(Gtk::ResponseType::OK));
    dialog->add_button("关闭", static_cast<int>(Gtk::ResponseType::CANCEL));
    dialog->signal_response().connect(
        [this, dialog, view, function_id](int response) {
            if (response == static_cast<int>(Gtk::ResponseType::OK)
                && m_learning_store) {
                const auto progress =
                    m_learning_store->load_progress(function_id);
                m_learning_store->save_progress(
                    function_id,
                    progress.status,
                    string(view->get_buffer()->get_text().raw()));
            }
            dialog->hide();
        });
    dialog->show();
}

void MainWindow::show_history_dialog(
    const string& function_id,
    const string& source_path,
    const string& member_name,
    const string& topic_title) {
    if (!m_learning_store) {
        return;
    }
    const auto runs = m_learning_store->recent_runs(function_id, 20);
    const string current_hash =
        member_source_hash(m_content_loader, source_path, member_name);

    auto dialog = Gtk::make_managed<Gtk::Dialog>();
    dialog->set_title("运行历史：" + topic_title);
    dialog->set_transient_for(*this);
    dialog->set_modal(true);
    dialog->set_default_size(780, 520);

    auto* content = dialog->get_content_area();
    auto paned = Gtk::make_managed<Gtk::Paned>(Gtk::Orientation::VERTICAL);
    paned->set_position(200);
    paned->set_hexpand(true);
    paned->set_vexpand(true);
    paned->set_shrink_start_child(false);
    paned->set_shrink_end_child(false);

    auto list_scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    list_scrolled->set_policy(
        Gtk::PolicyType::AUTOMATIC, Gtk::PolicyType::AUTOMATIC);
    auto list = Gtk::make_managed<Gtk::ListBox>();
    list->set_selection_mode(Gtk::SelectionMode::SINGLE);
    list->add_css_class("topic-list");
    list_scrolled->set_child(*list);

    auto output_scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    output_scrolled->set_policy(
        Gtk::PolicyType::AUTOMATIC, Gtk::PolicyType::AUTOMATIC);
    auto output_view = Gtk::make_managed<Gtk::TextView>();
    output_view->set_editable(false);
    output_view->set_cursor_visible(false);
    output_view->set_wrap_mode(Gtk::WrapMode::WORD_CHAR);
    output_view->add_css_class("code-view");
    output_scrolled->set_child(*output_view);

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
        auto output_by_row = make_shared<std::map<Gtk::ListBoxRow*, string>>();
        for (const auto& run : runs) {
            string code_state = "代码版本未知";
            if (!run.source_hash.empty() && !current_hash.empty()) {
                code_state =
                    run.source_hash == current_hash ? "代码一致" : "代码已修改";
            }
            auto row = Gtk::make_managed<Gtk::ListBoxRow>();
            auto label = Gtk::make_managed<Gtk::Label>(
                format_timestamp(run.ran_at) + " · "
                + format_duration_ms(run.duration_ms) + " · " + code_state);
            label->set_halign(Gtk::Align::START);
            label->set_margin_top(6);
            label->set_margin_bottom(6);
            label->set_margin_start(10);
            label->set_margin_end(10);
            row->set_child(*label);
            (*output_by_row)[row] = run.output;
            list->append(*row);
        }
        list->signal_row_selected().connect(
            [output_view, output_by_row](Gtk::ListBoxRow* row) {
                const auto found = output_by_row->find(row);
                if (found != output_by_row->end()) {
                    output_view->get_buffer()->set_text(found->second);
                }
            });        if (auto* first = list->get_row_at_index(0)) {
            list->select_row(*first);
        }
    }

    paned->set_start_child(*list_scrolled);
    paned->set_end_child(*output_scrolled);
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

    const string source_hash =
        member_source_hash(m_content_loader, source_path, member_name);

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
        [this, experiment_status_label, alive = m_ui_alive, started]() -> bool {
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
         source_hash,
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
                 source_hash,
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
                        learning_store->record_run(
                            function_id,
                            raw_output,
                            duration_ms,
                            source_hash);
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
    Gtk::Button* history_button) {
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
    const string chapter_name = chapter.name;
    auto current_topic = make_shared<TopicSelection>();
    if (history_button) {
        history_button->signal_clicked().connect(
            [this, current_topic]() {
                if (!current_topic->function_id.empty()) {
                    show_history_dialog(
                        current_topic->function_id,
                        current_topic->source_path,
                        current_topic->member_name,
                        current_topic->title);
                }
            });
    }
    auto activate_topic = make_shared<function<void(Gtk::ListBoxRow*)>>(
        [this,
         selection_by_row,
         current_topic,
         knowledge_description_label,
         source_view,
         result_view,
         category_name,
         chapter_name,
         experiment_spinner,
         experiment_status_label,
         history_button](Gtk::ListBoxRow* row) {
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
            display_source(
                source_view,
                m_content_loader,
                found->second.source_path,
                found->second.member_name);

            *current_topic = found->second;
            if (history_button) {
                history_button->set_sensitive(true);
            }

            if (!result_view) {
                return;
            }
            const string function_id = make_function_id(
                category_name,
                chapter_name,
                found->second.member_name);
            if (!m_function_registry.contains(function_id)) {
                return;
            }
            start_experiment(
                function_id,
                found->second.source_path,
                found->second.member_name,
                *result_view,
                experiment_spinner,
                experiment_status_label);
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
        row->set_selectable(true);
        row->set_activatable(true);
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
        };

        auto row_box = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL,
            12);
        row_box->append(*create_icon(subchapter.icon, 20));

        auto text_box = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::VERTICAL,
            4);
        text_box->set_hexpand(true);

        auto point_title = Gtk::make_managed<Gtk::Label>(subchapter.title);
        point_title->set_halign(Gtk::Align::START);
        point_title->add_css_class("heading");
        text_box->append(*point_title);

        auto point_description =
            Gtk::make_managed<Gtk::Label>(subchapter.description);
        point_description->set_halign(Gtk::Align::START);
        point_description->set_xalign(0);
        point_description->set_wrap(true);
        point_description->add_css_class("dim-label");
        text_box->append(*point_description);
        row_box->append(*text_box);

        if (m_learning_store) {
            auto note_button = Gtk::make_managed<Gtk::Button>("笔记");
            note_button->add_css_class("btn-sm");
            note_button->set_valign(Gtk::Align::CENTER);
            note_button->set_tooltip_text("编辑该知识点的学习笔记");
            note_button->signal_clicked().connect(
                [this, function_id, topic_title = subchapter.title]() {
                    show_note_dialog(function_id, topic_title);
                });
            row_box->append(*note_button);

            auto status_button = Gtk::make_managed<Gtk::Button>();
            status_button->add_css_class("btn-sm");
            status_button->set_valign(Gtk::Align::CENTER);
            status_button->set_tooltip_text(
                "点击切换掌握状态：未学 → 已学 → 需复习");
            auto status_text = Gtk::make_managed<Gtk::Label>();
            status_button->set_child(*status_text);
            auto apply_status = [status_text](int status) {
                static const array<pair<const char*, const char*>, 3> meta = {{
                    {"未学", "topic-status-new"},
                    {"已学", "topic-status-learned"},
                    {"需复习", "topic-status-review"},
                }};
                for (const auto& entry : meta) {
                    status_text->remove_css_class(entry.second);
                }
                status_text->set_text(meta[status].first);
                status_text->add_css_class(meta[status].second);
            };
            const int initial_status =
                m_learning_store->load_progress(function_id).status;
            apply_status(initial_status);
            auto status_value = make_shared<int>(initial_status);
            status_button->signal_clicked().connect(
                [this, function_id, status_value, apply_status]() {
                    *status_value = (*status_value + 1) % 3;
                    apply_status(*status_value);
                    const auto progress =
                        m_learning_store->load_progress(function_id);
                    m_learning_store->save_progress(
                        function_id,
                        *status_value,
                        progress.note);
                });
            row_box->append(*status_button);
        }

        auto run = Gtk::make_managed<Gtk::Button>("运行");
        run->add_css_class("suggested-action");
        run->add_css_class("btn-primary");
        run->add_css_class("btn-sm");
        run->add_css_class("topic-run");
        const bool can_run = m_function_registry.contains(function_id);
        run->set_sensitive(can_run);
        run->set_tooltip_text(can_run
            ? "运行该知识点的实验代码"
            : "该知识点尚未实现可运行实验");
        if (can_run && result_view) {
            run->signal_clicked().connect(
                [row,
                 topics_list = &topics_list,
                 activate_topic]() {
                    topics_list->select_row(*row);
                    (*activate_topic)(row);
                });
        }
        row_box->append(*run);

        row->set_child(*row_box);
        topics_list.append(*row);
    }

    topics_list.signal_row_selected().connect(
        [activate_topic](Gtk::ListBoxRow* row) {
            (*activate_topic)(row);
        });
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
