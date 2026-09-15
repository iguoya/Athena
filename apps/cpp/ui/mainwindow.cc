#include "ui/mainwindow.h"

#include "platform/menu_bar_platform.h"
#include "platform/app_paths.h"
#include "registry/domain_graph.h"
#include "ui/external_app_launcher.h"
#include "registry/knowledge_graph.h"
#include "render/domain_graph_view.h"
#include "services/experiment_runner.h"
#include "ui/about_dialog.h"
#include "ui/chapter_index_page.h"
#include "ui/chapter_page_stack.h"
#include "ui/chapter_overview.h"
#include "ui/code_chapter_page.h"
#include "ui/experiment_page.h"
#include "ui/pocket_cube_page.h"
#include "ui/progress_overview.h"
#include "ui/lesson_figures.h"
#include "ui/lesson_page.h"
#include "ui/type_semantics_lesson_page.h"

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

string index_page_key(const string& category_name) {
    return category_name + ".__index__";
}

constexpr const char* kCppCategory = "cpp";
// 数据驱动学习页的控件名，由 lesson_page.blp 的根控件名派生（ADR 0055）。
constexpr const char* kDataLessonPageWidget = "lesson_page";
constexpr const char* kPracticeCubePageWidget = "practice_cube_page";
// 由 athena.json 的 chapter.ui.blueprint 派生：blueprint 文件名去掉
// .blp 后缀再加 _page，见 scripts/project_generator/model.py。
constexpr const char* kTypeSemanticsLessonPageWidget =
    "type_semantics_lesson_page";

} // namespace

MainWindow::MainWindow(
    BaseObjectType* cobject,
    const Glib::RefPtr<Gtk::Builder>& builder)
    : Gtk::ApplicationWindow(cobject),
      m_main_builder(builder),
      m_content_loader(),
      m_function_registry(create_default_function_registry()) {
    // 用 window.blp 里的适中默认尺寸作为初始大小，让窗口正常居中出现并
    // 保留可见的系统标题栏。最大化和全屏都由用户自己选择。

    auto css = Gtk::CssProvider::create();
    css->load_from_resource("/app/style.css");
    Gtk::StyleContext::add_provider_for_display(
        get_display(), css, GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    Gtk::IconTheme::get_for_display(get_display())->add_resource_path("/app/icons");
    Gtk::Window::set_default_icon_name("cn.athena.icon");

    m_root_stack = m_main_builder->get_widget<Gtk::Stack>("root_stack");
    m_home_graph = m_main_builder->get_widget<Gtk::Box>("home_graph");
    m_breadcrumb_box =
        m_main_builder->get_widget<Gtk::Box>("breadcrumb_box");
    auto* home_page = m_main_builder->get_widget<Gtk::Box>("home_page");
    auto* content_area = m_main_builder->get_widget<Gtk::Box>("content_area");
    m_home_button = m_main_builder->get_widget<Gtk::Button>("home_button");
    auto* experiment_page =
        m_main_builder->get_widget<Gtk::Box>("experiment_page");
    auto* app_menu_bar =
        m_main_builder->get_widget<Gtk::PopoverMenuBar>("app_menu_bar");
    auto* chapter_stack =
        m_main_builder->get_widget<Gtk::Stack>("chapter_stack");
    m_chapter_switcher =
        m_main_builder->get_widget<Gtk::MenuButton>("chapter_switcher");
    if (!m_root_stack || !m_home_graph || !m_breadcrumb_box || !home_page
        || !content_area || !experiment_page || !m_home_button || !app_menu_bar
        || !chapter_stack || !m_chapter_switcher) {
        throw runtime_error("Failed to get required widgets from main UI");
    }
    m_root_stack->add(*home_page, "home", "首页");
    m_root_stack->add(*content_area, "category", "分类");
    m_root_stack->add(*experiment_page, "experiment", "专注实验");
    m_root_stack->set_visible_child("home");
    m_pages = make_unique<ChapterPageStack>(*chapter_stack);

    load_chapter_metadata();
    // 首次进入分类会立即构建进度页，所以存储和依赖它的模块必须先完成
    // 初始化。
    open_learning_store();
    m_dialogs = make_unique<LearningDialogs>(
        *this, m_content_loader, m_learning_store.get(), m_ui_alive);
    m_experiment_runner = make_unique<ExperimentRunner>(
        m_function_registry, m_ui_alive);
    m_experiment_page = make_unique<ExperimentPage>(
        m_main_builder,
        m_content_loader,
        *m_experiment_runner,
        m_ui_alive,
        [this]() { return_from_experiment(); });
    m_about_dialog = make_unique<AboutDialog>(*this);

    setup_menu();
    app_menu_bar->set_menu_model(m_menu_model);
    // macOS 上系统标准菜单栏已经接管同一份菜单模型，窗口内这条菜单栏
    // 只在没有这层系统集成的平台（目前是 Ubuntu）显示，避免重复。
    app_menu_bar->set_visible(!platform_has_native_menu_bar());

    m_home_button->signal_clicked().connect([this]() { go_home(); });
    build_home_graph();
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
    // 进度随仓库走（ADR 0053）：工作树里写 apps/cpp/progress/，换一台机器
    // clone 下来掌握度还在。发行包拿不到仓库路径，退回本机用户数据目录。
    const string own_root = own_app_root();
    const string data_dir = own_root.empty()
        ? Glib::build_filename(Glib::get_user_data_dir(), "Athena")
        : Glib::build_filename(own_root, "progress");
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

void MainWindow::build_home_graph() {
    // 掌握度口径与分类内知识图谱、进度页一致：知识点 ID -> 星级。
    std::map<string, int> mastery_by_id;
    if (m_learning_store) {
        try {
            mastery_by_id = m_learning_store->load_all_mastery();
        } catch (const exception& error) {
            cerr << "Failed to load mastery stats for home graph: "
                 << error.what() << endl;
        }
    }

    const DomainGraph graph = build_domain_graph(m_catalog, mastery_by_id);
    // 领域节点有两种去处：本程序里的分类，或 apps/ 下的独立应用（ADR 0032）。
    // 图谱只说这个领域由谁承载，怎么打开由这里决定。
    // std:: 不能省：Gtk::Widget 有成员函数 map()，裸写会被解析成它。
    std::map<string, string> app_by_domain;
    for (const auto& node : graph.nodes) {
        if (node.kind == DomainKind::ExternalApp && !node.app_id.empty()) {
            app_by_domain[node.id] = node.app_id;
        }
    }
    auto* view = make_domain_graph_view(
        graph,
        [this, app_by_domain](const string& domain_id) {
            const auto found = app_by_domain.find(domain_id);
            if (found == app_by_domain.end()) {
                enter_category(domain_id);
                return;
            }
            launch_domain_app(found->second);
        });
    m_home_graph->append(*view);
}

void MainWindow::launch_domain_app(const string& app_id) {
    const string apps_root = external_apps_root();
    for (const auto& app : discover_external_apps(apps_root)) {
        if (app.id != app_id) {
            continue;
        }
        // 独立应用自己建库、自己迁移（ADR 0037），主程序不传学习库路径，
        // 也不假设两边的表结构还能对上。
        if (const auto error = launch_external_app(app)) {
            // 未构建或启动失败都只是提示：外部应用可不可用不影响主程序。
            auto* notice = Gtk::make_managed<Gtk::MessageDialog>(
                *this, *error, false, Gtk::MessageType::INFO,
                Gtk::ButtonsType::OK, true);
            notice->signal_response().connect([notice](int) { notice->hide(); });
            notice->show();
        }
        return;
    }

    // 独立应用不随主程序 .app 分发，所以两种"找不到"要分开说：
    // 装好的发行包里根本没有 apps/，让用户去检查 app.json 是误导。
    const string message = apps_root.empty()
        ? "「" + app_id + "」是独立应用，不包含在当前发行包里。\n\n"
              "请到源码仓库的 apps/" + app_id
              + " 目录按该应用自己的 README / AGENTS.md 用开发模式启动"
                "（Tauri 应用执行 ./scripts/dev.sh），不要打开 /Applications 里的打包副本。"
        : "在 " + apps_root + " 下没有找到独立应用 " + app_id
              + "，请检查 " + app_id + "/app.json 是否存在。";
    auto* missing = Gtk::make_managed<Gtk::MessageDialog>(
        *this, message, false, Gtk::MessageType::WARNING, Gtk::ButtonsType::OK,
        true);
    missing->signal_response().connect([missing](int) { missing->hide(); });
    missing->show();
}

void MainWindow::show_about_dialog() {
    m_about_dialog->present();
}

void MainWindow::show_settings_dialog() {
    m_dialogs->show_settings();
}

void MainWindow::go_home() {
    clear_breadcrumb();
    m_home_button->set_visible(true);
    m_chapter_switcher->set_visible(false);
    m_root_stack->set_visible_child("home");
}

string MainWindow::category_title(const string& category_name) const {
    for (const auto& category : m_catalog.categories()) {
        if (category.name == category_name) {
            return category.title;
        }
    }
    return category_name;
}

void MainWindow::enter_category(const string& category_name) {
    if (category_name != m_current_category) {
        m_current_category = category_name;
        build_category(category_name);
    }
    m_root_stack->set_visible_child("category");
    m_home_button->set_visible(true);
    m_chapter_switcher->set_visible(true);
    show_category_index(category_name);
}

void MainWindow::show_category_index(const string& category_name) {
    // C++ 目录就是实时知识图谱，返回目录时按最新自测成绩重建节点颜色和
    // 完成进度。其余分类的静态网格无需重复装配。
    if (category_name == kCppCategory && m_pages &&
        m_pages->has_page(index_page_key(category_name))) {
        m_pages->set_page(
            index_page_key(category_name),
            *create_index_page(category_name),
            "学习图谱");
    }
    m_pages->show(index_page_key(category_name));
    show_category_breadcrumb(category_name);
    m_chapter_switcher->set_label("目录");
}

void MainWindow::clear_breadcrumb() {
    while (auto* child = m_breadcrumb_box->get_first_child()) {
        m_breadcrumb_box->remove(*child);
    }
}

void MainWindow::show_category_breadcrumb(const string& category_name) {
    clear_breadcrumb();
    m_breadcrumb_box->append(*Gtk::make_managed<Gtk::Label>("›"));

    auto* link = Gtk::make_managed<Gtk::Button>(category_title(category_name));
    link->set_has_frame(false);
    link->add_css_class("breadcrumb-link");
    link->set_tooltip_text("返回" + category_title(category_name) + "章节索引");
    link->signal_clicked().connect(
        [this, category_name]() { show_category_index(category_name); });
    m_breadcrumb_box->append(*link);
}

void MainWindow::show_chapter_breadcrumb(
    const string& category_name,
    const string& trailing) {
    show_category_breadcrumb(category_name);
    m_breadcrumb_box->append(*Gtk::make_managed<Gtk::Label>("›"));
    m_breadcrumb_box->append(*Gtk::make_managed<Gtk::Label>(trailing));
}

const ChapterMeta* MainWindow::find_chapter_by_key(
    const string& category_name,
    const string& page_key) const {
    const auto category = m_catalog.chapters().find(category_name);
    if (category == m_catalog.chapters().end()) {
        return nullptr;
    }
    for (const auto& chapter : category->second) {
        if (chapter_key(category_name, chapter.name) == page_key) {
            return &chapter;
        }
    }
    return nullptr;
}

void MainWindow::navigate_to(
    const string& category_name,
    const string& page_key) {
    if (page_key == index_page_key(category_name)) {
        show_category_index(category_name);
          } else if (const auto* chapter =
                   find_chapter_by_key(category_name, page_key)) {
        open_chapter(category_name, *chapter);
    }
}

void MainWindow::open_chapter(
    const string& category_name,
    const ChapterMeta& chapter) {
    ensure_chapter_page(category_name, chapter);
    const string page_key = chapter_key(category_name, chapter.name);
    m_pages->show(page_key);
    show_chapter_breadcrumb(category_name, chapter.title);
    m_chapter_switcher->set_label(chapter.title);
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
    m_pages->set_page(page_key, *widget, chapter.title);

    auto overview_requested = [this, chapter]() {
        handle_chapter_overview(chapter);
    };
    auto experiment_requested =
        [this](const ExperimentSelection& experiment, bool run_immediately) {
            show_experiment(experiment, run_immediately);
        };
    if (chapter.widget_name == "chapter_page") {
        m_code_pages[page_key] = make_unique<CodeChapterPage>(
            chapter,
            builder,
            m_function_registry,
            m_learning_store.get(),
            *m_dialogs,
            experiment_requested,
            overview_requested,
            [this]() { refresh_progress_page(); });
    } else if (chapter.widget_name == kDataLessonPageWidget) {
        // 课文里的 figure 块按 id 取控件。本章暂时全用表格与代码块表达，
        // 需要自绘图时在这里注册，数据只决定它出现在哪一节（ADR 0055）。
        m_lesson_pages[page_key] = make_unique<LessonPage>(
            chapter, builder, make_lesson_figure, experiment_requested);
    } else if (chapter.widget_name == kPracticeCubePageWidget) {
        m_pocket_cube_pages[page_key] = make_unique<PocketCubePage>(
            chapter, builder, m_content_loader, overview_requested);
       } else if (chapter.widget_name == kTypeSemanticsLessonPageWidget) {
        std::map<string, int> mastery_by_id;
        if (m_learning_store) {
            try {
                mastery_by_id = m_learning_store->load_all_mastery();
            } catch (const exception& error) {
                cerr << "Failed to load mastery stats for lesson tabs: "
                     << error.what() << endl;
            }
        }
        m_type_semantics_lesson_pages[page_key] =
            make_unique<TypeSemanticsLessonPage>(
                chapter,
                builder,
                mastery_by_id,
                experiment_requested,
                // 随堂考核的成绩按知识点落库；页面不碰 LearningStore，
                // 写库连同失败处理都留在这一层。
                [this](const string& function_id,
                       int mastery,
                       int correct,
                       int total) {
                    if (!m_learning_store) {
                        return false;
                    }
                    try {
                        m_learning_store->save_assessment(
                            function_id, mastery, correct, total);
                        refresh_progress_page();
                        return true;
                    } catch (const exception& error) {
                        cerr << "Failed to save checkpoint score for "
                             << function_id << ": " << error.what() << endl;
                        return false;
                    }
                });
    }
    m_loaded_chapters.insert(page_key);
}

void MainWindow::show_experiment(
    const ExperimentSelection& experiment, bool run_immediately) {
    // 第一次进入当前实验时保存来源页。若用户在实验仍运行时已经返回并
    // 再次点了别的实验，只带回正在运行的实验，不覆盖它原来的返回目标。
    if (!m_experiment_runner->running()) {
        m_experiment_return_category = m_current_category;
        m_experiment_return_page_key = m_pages->current_key();
    }

    m_root_stack->set_visible_child("experiment");
    m_home_button->set_visible(false);
    m_chapter_switcher->set_visible(false);
    show_chapter_breadcrumb(
        m_current_category, "专注实验 · " + experiment.title);
    m_experiment_page->show(experiment, run_immediately);
}

void MainWindow::return_from_experiment() {
    if (m_experiment_return_category.empty()
        || m_experiment_return_page_key.empty()) {
        go_home();
        return;
    }

    m_root_stack->set_visible_child("category");
    m_home_button->set_visible(true);
    m_chapter_switcher->set_visible(true);
    navigate_to(
        m_experiment_return_category, m_experiment_return_page_key);
}

void MainWindow::build_category(const string& category_name) {
    m_pages->reset();

    m_pages->set_page(
        index_page_key(category_name),
        *create_index_page(category_name),
        "章节");

    const auto category = m_catalog.chapters().find(category_name);
    if (category != m_catalog.chapters().end()) {
        for (const auto& chapter : category->second) {
            const string page_key = chapter_key(category_name, chapter.name);
            if (m_loaded_chapters.count(page_key) == 0) {
                m_pages->set_placeholder(page_key, chapter.title);
                continue;
            }
            const auto builder = get_chapter_builder(category_name, chapter.name);
            auto* widget = builder
                ? builder->get_widget<Gtk::Widget>(chapter.widget_name)
                : nullptr;
            if (widget) {
                m_pages->set_page(page_key, *widget, chapter.title);
            } else {
                m_pages->set_placeholder(page_key, chapter.title);
                cerr << "Failed to get root widget '" << chapter.widget_name
                     << "' for " << page_key << endl;
            }
        }
    }

    rebuild_chapter_switcher(category_name);
}

Gtk::Widget* MainWindow::create_index_page(const string& category_name) {
    ChapterIndexSpec spec;
    spec.category_title = category_title(category_name);

    const auto category = m_catalog.chapters().find(category_name);
    if (category != m_catalog.chapters().end()) {
        for (const auto& chapter : category->second) {
            spec.chapters.push_back(
                {.key = chapter_key(category_name, chapter.name),
                 .title = chapter.title,
                 .description = chapter.description,
                 .icon = chapter.icon});
        }
    }

    if (category_name == kCppCategory) {
        // 图谱要显示逐个知识点的掌握与考核成绩，所以取完整评定记录，
        // 不只是熟练度数字。
        std::map<string, KnowledgeProgressRecord> progress;
        if (m_learning_store) {
            try {
                for (const auto& [function_id, assessment] :
                     m_learning_store->load_all_assessments()) {
                    progress[function_id] = KnowledgeProgressRecord{
                        .mastery = assessment.mastery,
                        .correct = assessment.correct,
                        .total = assessment.total,
                    };
                }
            } catch (const exception& error) {
                cerr << "Failed to load mastery stats: " << error.what()
                     << endl;
            }
        }
        spec.knowledge_graph = build_knowledge_graph(
            m_catalog, category_name, progress);
        std::map<string, int> mastery_only;
        for (const auto& [function_id, record] : progress) {
            mastery_only[function_id] = record.mastery;
        }
        // 进度概览与图谱合一：概览放图谱上方，逐条进度画在章节卡片上，
        // 不再单开「学习进度」页。
        spec.progress = aggregate_category_progress(
            m_catalog, category_name, mastery_only);
    }
    spec.on_open = [this, category_name](const string& page_key) {
        navigate_to(category_name, page_key);
    };
    spec.on_open_chapter = [this, category_name](const string& chapter_name) {
        if (const auto* chapter =
                m_catalog.find_chapter(category_name, chapter_name)) {
            open_chapter(category_name, *chapter);
        }
    };
    return make_chapter_index_page(spec);
}

void MainWindow::rebuild_chapter_switcher(const string& category_name) {
    auto* list = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 2);
    list->add_css_class("chapter-switcher-list");

    auto add_entry = [this, category_name, list](
                         const string& page_key, const string& label) {
        auto* text = Gtk::make_managed<Gtk::Label>(label);
        text->set_xalign(0.0F);
        text->set_hexpand(true);
        auto* button = Gtk::make_managed<Gtk::Button>();
        button->add_css_class("flat");
        button->set_has_frame(false);
        button->set_child(*text);
        button->signal_clicked().connect(
            [this, category_name, page_key]() {
                if (auto* popover = m_chapter_switcher->get_popover()) {
                    popover->popdown();
                }
                navigate_to(category_name, page_key);
            });
        list->append(*button);
    };

    add_entry(index_page_key(category_name), "目录");
    const auto category = m_catalog.chapters().find(category_name);
    if (category != m_catalog.chapters().end()) {
        for (const auto& chapter : category->second) {
            add_entry(
                chapter_key(category_name, chapter.name), chapter.title);
        }
    }

    auto* scroller = Gtk::make_managed<Gtk::ScrolledWindow>();
    scroller->set_policy(Gtk::PolicyType::NEVER, Gtk::PolicyType::AUTOMATIC);
    scroller->set_propagate_natural_height(true);
    scroller->set_max_content_height(560);
    scroller->set_child(*list);

    auto* popover = Gtk::make_managed<Gtk::Popover>();
    popover->set_child(*scroller);
    m_chapter_switcher->set_popover(*popover);
}

// 熟练度变化后刷新受影响的界面。进度已经不是单独一页：概览在学习图谱页
// 顶部，逐条进度在图谱的章节卡片上，所以这里重建索引页即可。
void MainWindow::refresh_progress_page() {
    if (!m_type_semantics_lesson_pages.empty()) {
        std::map<string, int> mastery_by_id;
        if (m_learning_store) {
            try {
                mastery_by_id = m_learning_store->load_all_mastery();
            } catch (const exception& error) {
                cerr << "Failed to reload mastery stats for lesson tabs: "
                     << error.what() << endl;
            }
        }
        for (const auto& [page_key, lesson_page] :
             m_type_semantics_lesson_pages) {
            lesson_page->refresh_progress(mastery_by_id);
        }
    }

    // 索引页是缓存的，熟练度变了要重建才能反映到概览与章节卡片上。
    const string key = index_page_key(kCppCategory);
    if (!m_pages || !m_pages->has_page(key)) {
        return;
    }
    const bool was_visible = m_pages->current_key() == key;
    m_pages->set_page(key, *create_index_page(kCppCategory), "学习图谱");
    if (was_visible) {
        m_pages->show(key);
    }
}

void MainWindow::handle_chapter_overview(const ChapterMeta& chapter) {
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
