#include "mainwindow.h"

#include "app_icon.h"
#include "services/experiment_runner.h"
#include "ui/about_dialog.h"
#include "ui/chapter_nav_strip.h"
#include "ui/chapter_overview.h"
#include "ui/code_chapter_page.h"
#include "ui/handbook_page.h"
#include "ui/icon_utils.h"
#include "ui/pocket_cube_page.h"
#include "ui/progress_page.h"

#include <algorithm>
#include <iostream>
#include <stdexcept>

using namespace std;

namespace {

string chapter_key(const string& category_name, const string& chapter_name) {
    return category_name + "." + chapter_name;
}

string handbook_page_key(const string& category_name) {
    return category_name + ".__handbook__";
}

constexpr const char* kWelcomePageWidget = "welcome_page";
constexpr const char* kPracticeCubePageWidget = "practice_cube_page";
constexpr const char* kProgressPageKey = "__progress__";

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
        get_display(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    Gtk::IconTheme::get_for_display(get_display())->add_resource_path("/app/icons");
    Gtk::Window::set_default_icon_name("cn.athena.icon");

    m_category_sidebar =
        m_main_builder->get_widget<Gtk::Box>("category_sidebar");
    auto* chapter_stack =
        m_main_builder->get_widget<Gtk::Stack>("chapter_stack");
    auto* chapter_tab_box =
        m_main_builder->get_widget<Gtk::FlowBox>("chapter_tab_box");
    auto settings_button =
        m_main_builder->get_widget<Gtk::Button>("settings_button");
    auto about_button =
        m_main_builder->get_widget<Gtk::Button>("about_button");
    if (!m_category_sidebar || !chapter_stack || !chapter_tab_box
        || !settings_button || !about_button) {
        throw runtime_error("Failed to get required widgets from main UI");
    }
    m_nav = make_unique<ChapterNavStrip>(*chapter_tab_box, *chapter_stack);

    load_chapter_metadata();
    // 首个分类按钮激活时会立即构建进度页，所以存储和依赖它的模块必须
    // 先完成初始化。
    open_learning_store();
    m_dialogs = make_unique<LearningDialogs>(
        *this, m_content_loader, m_learning_store.get(), m_ui_alive);
    m_experiment_runner = make_unique<ExperimentRunner>(
        m_function_registry,
        m_content_loader,
        m_learning_store.get(),
        ATHENA_SOURCE_ROOT,
        m_ui_alive);
    m_about_dialog = make_unique<AboutDialog>(*this);

    settings_button->signal_clicked().connect(
        [this]() { m_dialogs->show_settings(); });
    about_button->signal_clicked().connect(
        [this]() { m_about_dialog->present(); });
    setup_category_sidebar();
}

MainWindow::~MainWindow() {
    // 页面、对话框和后台执行器的延迟回调都先检查这份共享状态。
    m_ui_alive->store(false);
}

void MainWindow::load_chapter_metadata() {
    const string source =
        m_content_loader.load_resource("/app/data/chapter_catalog.json");
    if (source.empty()) {
        throw runtime_error("generated chapter Catalog not found in GResource");
    }
    m_catalog = ChapterCatalog::from_runtime_json(source);
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

void MainWindow::setup_category_sidebar() {
    Gtk::ToggleButton* group_owner = nullptr;
    for (const auto& category : m_catalog.categories()) {
        auto button = Gtk::make_managed<Gtk::ToggleButton>();
        button->add_css_class("nav-button");
        button->set_tooltip_text(category.description);

        auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
        box->set_valign(Gtk::Align::CENTER);
        box->set_margin_top(12);
        box->set_margin_bottom(12);
        box->append(*make_icon_image(category.icon, 24));
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

void MainWindow::ensure_chapter_page(
    const string& category_name,
    const ChapterMeta& chapter) {
    const string page_key = chapter_key(category_name, chapter.name);
    if (m_loaded_chapters.count(page_key) > 0) {
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
    m_nav->set_page(page_key, *widget, chapter.title);

    auto overview_requested = [this, chapter]() {
        handle_chapter_overview(chapter);
    };
    if (chapter.widget_name == "chapter_page") {
        m_code_pages[page_key] = make_unique<CodeChapterPage>(
            chapter,
            builder,
            m_content_loader,
            m_function_registry,
            m_learning_store.get(),
            *m_dialogs,
            *m_experiment_runner,
            overview_requested,
            [this]() { refresh_progress_page(); });
    } else if (chapter.widget_name == kPracticeCubePageWidget) {
        m_pocket_cube_pages[page_key] = make_unique<PocketCubePage>(
            chapter, builder, m_content_loader, overview_requested);
    }
    // 欢迎页等特殊静态页只需构建 Blueprint 控件树。
    m_loaded_chapters.insert(page_key);
}

void MainWindow::build_chapter_tabs(const string& category_name) {
    m_nav->reset();

    const auto category = m_catalog.chapters().find(category_name);
    if (category == m_catalog.chapters().end() || category->second.empty()) {
        auto* placeholder = Gtk::make_managed<Gtk::Label>("该分类暂无章节");
        placeholder->set_halign(Gtk::Align::CENTER);
        placeholder->set_valign(Gtk::Align::CENTER);
        m_nav->set_page(category_name + ".__empty__", *placeholder, "空");
        return;
    }

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
        if (m_loaded_chapters.count(page_key) > 0) {
            const auto builder = get_chapter_builder(category_name, chapter.name);
            auto* widget = builder
                ? builder->get_widget<Gtk::Widget>(chapter.widget_name)
                : nullptr;
            if (widget) {
                m_nav->set_page(page_key, *widget, chapter.title);
            } else {
                cerr << "Failed to get root widget '" << chapter.widget_name
                     << "' for " << page_key << endl;
            }
        } else {
            m_nav->set_placeholder(page_key, chapter.title);
        }

        m_nav->add_tab(
            {.key = page_key,
             .label = chapter.title,
             .tooltip = chapter.description,
             .icon = chapter.icon},
            [this, category_name, chapter, page_key]() {
                ensure_chapter_page(category_name, chapter);
                m_nav->reveal(page_key);
            });

        if (chapter.widget_name == kWelcomePageWidget) {
            append_progress_tab();
            append_handbook_tab(category_name);
        }
    }

    m_nav->activate_first();
}

Gtk::Widget* MainWindow::create_progress_page() {
    std::map<string, int> mastery_by_id;
    if (m_learning_store) {
        try {
            mastery_by_id = m_learning_store->load_all_mastery();
        } catch (const exception& error) {
            cerr << "Failed to load mastery stats: " << error.what() << endl;
        }
    }
    return make_progress_page(
        "C++", aggregate_category_progress(m_catalog, "cpp", mastery_by_id));
}

void MainWindow::append_progress_tab() {
    m_nav->set_page(kProgressPageKey, *create_progress_page(), "学习进度");
    m_nav->add_tab(
        {.key = kProgressPageKey,
         .label = "学习进度",
         .tooltip = "各章节知识点的掌握情况统计",
         .icon = {.type = "theme", .name = "utilities-system-monitor-symbolic"}},
        [this]() {
            refresh_progress_page();
            m_nav->reveal(kProgressPageKey);
        });
}

void MainWindow::refresh_progress_page() {
    if (!m_nav || !m_nav->has_page(kProgressPageKey)) {
        return;
    }
    const bool was_visible = m_nav->current_key() == kProgressPageKey;
    m_nav->set_page(kProgressPageKey, *create_progress_page(), "学习进度");
    if (was_visible) {
        m_nav->reveal(kProgressPageKey);
    }
}

void MainWindow::append_handbook_tab(const string& category_name) {
    m_nav->add_tab(
        {.key = handbook_page_key(category_name),
         .label = "手册",
         .tooltip = "本分类的手册：理论、原则与工程思想",
         .icon = {.type = "theme", .name = "accessories-dictionary-symbolic"}},
        [this, category_name]() { show_handbook_page(category_name); });
}

void MainWindow::ensure_handbook_page(const string& category_name) {
    if (m_handbook_pages.count(category_name) > 0) {
        return;
    }
    auto page = make_unique<HandbookPage>(
        category_name,
        m_catalog.handbook_documents(category_name),
        m_content_loader,
        *this);
    // 手册页常驻 Stack：切换分类时不销毁，ArticleView 生命周期由页面对象独占。
    m_nav->set_page(
        handbook_page_key(category_name),
        page->widget(),
        "手册",
        ChapterNavStrip::Persistence::Persistent);
    m_handbook_pages[category_name] = std::move(page);
}

void MainWindow::show_handbook_page(
    const string& category_name,
    const string& jump_to_document) {
    ensure_handbook_page(category_name);
    m_nav->show(handbook_page_key(category_name));

    if (!jump_to_document.empty()) {
        m_handbook_pages.at(category_name)->scroll_to_document(jump_to_document);
    }
}

void MainWindow::handle_chapter_overview(const ChapterMeta& chapter) {
    if (!chapter.overview_document.empty()) {
        show_handbook_page(chapter.category, chapter.overview_document);
        return;
    }
    launch_local_chapter_overview(chapter);
}

Glib::RefPtr<Gtk::Builder> MainWindow::get_chapter_builder(
    const string& category_name,
    const string& chapter_name) {
    const string key = chapter_key(category_name, chapter_name);
    if (const auto cached = m_chapter_builders.find(key);
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
