#include "mainwindow.h"

#include "app_icon.h"
#include "menu_bar_platform.h"
#include "services/experiment_runner.h"
#include "ui/about_dialog.h"
#include "ui/chapter_nav_strip.h"
#include "ui/chapter_overview.h"
#include "ui/code_chapter_page.h"
#include "ui/handbook_page.h"
#include "ui/icon_utils.h"
#include "ui/pocket_cube_page.h"
#include "ui/progress_page.h"
#include "ui/workbench_page.h"

#include <giomm/menu.h>
#include <giomm/simpleaction.h>

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
// 由 athena.json 的 chapter.ui.blueprint 派生：blueprint 文件名去掉
// .blp 后缀再加 _page，见 scripts/project_generator/model.py。
constexpr const char* kWorkbenchPageWidget = "workbench_chapter_page";
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

    m_root_stack = m_main_builder->get_widget<Gtk::Stack>("root_stack");
    m_home_grid = m_main_builder->get_widget<Gtk::FlowBox>("home_grid");
    m_breadcrumb_label =
        m_main_builder->get_widget<Gtk::Label>("breadcrumb_label");
    auto* home_page = m_main_builder->get_widget<Gtk::Box>("home_page");
    auto* content_area = m_main_builder->get_widget<Gtk::Box>("content_area");
    auto* home_button = m_main_builder->get_widget<Gtk::Button>("home_button");
    auto* app_menu_bar =
        m_main_builder->get_widget<Gtk::PopoverMenuBar>("app_menu_bar");
    auto* chapter_stack =
        m_main_builder->get_widget<Gtk::Stack>("chapter_stack");
    auto* chapter_tab_box =
        m_main_builder->get_widget<Gtk::FlowBox>("chapter_tab_box");
    if (!m_root_stack || !m_home_grid || !m_breadcrumb_label || !home_page
        || !content_area || !home_button || !app_menu_bar || !chapter_stack
        || !chapter_tab_box) {
        throw runtime_error("Failed to get required widgets from main UI");
    }
    m_root_stack->add(*home_page, "home", "首页");
    m_root_stack->add(*content_area, "category", "分类");
    m_root_stack->set_visible_child("home");
    m_nav = make_unique<ChapterNavStrip>(*chapter_tab_box, *chapter_stack);

    load_chapter_metadata();
    // 首次进入分类会立即构建进度页，所以存储和依赖它的模块必须先完成
    // 初始化。
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

    setup_menu();
    app_menu_bar->set_menu_model(m_menu_model);
    // macOS 上系统标准菜单栏已经接管同一份菜单模型，窗口内这条菜单栏
    // 只在没有这层系统集成的平台（目前是 Ubuntu）显示，避免重复。
    app_menu_bar->set_visible(!platform_has_native_menu_bar());

    home_button->signal_clicked().connect([this]() { go_home(); });
    build_home_grid();
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

void MainWindow::setup_menu() {
    // 一个子菜单：macOS 的原生菜单栏会把它提升为系统标准的应用菜单
    // （标题被系统换成应用名），其他平台里它就是窗口内菜单栏上唯一的
    // 一个下拉项。两条路径共享同一份 win.* 动作，行为完全一致。
    m_menu_model = Gio::Menu::create();
    auto app_menu = Gio::Menu::create();
    app_menu->append("关于 Athena", "win.about");
    app_menu->append("设置…", "win.settings");
    auto quit_section = Gio::Menu::create();
    quit_section->append("退出 Athena", "win.quit");
    app_menu->append_section("", quit_section);
    m_menu_model->append_submenu("Athena", app_menu);

    add_action("settings", [this]() { m_dialogs->show_settings(); });
    add_action("about", [this]() { m_about_dialog->present(); });
    add_action("quit", [this]() {
        if (auto app = get_application()) {
            app->quit();
        } else {
            close();
        }
    });

    if (auto app = get_application()) {
        app->set_accel_for_action("win.quit", "<Primary>q");
        app->set_accel_for_action("win.settings", "<Primary>comma");
    }
}

void MainWindow::build_home_grid() {
    for (const auto& category : m_catalog.categories()) {
        auto tile = Gtk::make_managed<Gtk::Button>();
        tile->add_css_class("home-tile");
        tile->set_tooltip_text(category.description);

        auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 12);
        box->set_halign(Gtk::Align::CENTER);
        box->set_valign(Gtk::Align::CENTER);
        box->append(*make_icon_image(category.icon, 40));

        auto title = Gtk::make_managed<Gtk::Label>(category.title);
        title->add_css_class("home-tile-title");
        box->append(*title);

        auto description = Gtk::make_managed<Gtk::Label>(category.description);
        description->add_css_class("home-tile-desc");
        description->set_wrap(true);
        description->set_justify(Gtk::Justification::CENTER);
        description->set_max_width_chars(24);
        box->append(*description);

        tile->set_child(*box);
        tile->signal_clicked().connect(
            [this, category_name = category.name]() {
                enter_category(category_name);
            });
        m_home_grid->append(*tile);
    }
}

void MainWindow::show_about_dialog() {
    m_about_dialog->present();
}

void MainWindow::show_settings_dialog() {
    m_dialogs->show_settings();
}

void MainWindow::go_home() {
    m_breadcrumb_label->set_text("");
    m_root_stack->set_visible_child("home");
}

void MainWindow::enter_category(const string& category_name) {
    if (category_name != m_current_category) {
        m_current_category = category_name;
        build_chapter_tabs(category_name);
    }
    string title = category_name;
    for (const auto& category : m_catalog.categories()) {
        if (category.name == category_name) {
            title = category.title;
            break;
        }
    }
    m_breadcrumb_label->set_text("›  " + title);
    m_root_stack->set_visible_child("category");
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
    } else if (chapter.widget_name == kWorkbenchPageWidget) {
        m_workbench_pages[page_key] = make_unique<WorkbenchPage>(
            chapter, builder, m_content_loader, *m_experiment_runner, *this);
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
