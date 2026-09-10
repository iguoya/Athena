#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "ui/external_app_launcher.h"
#include "registry/function_registry.h"
#include "storage/learning_store.h"
#include "ui/learning_dialogs.h"

#include <gtkmm.h>

#include <atomic>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

using namespace std;

class AboutDialog;
class ChapterPageStack;
class CodeChapterPage;
class ExperimentPage;
class ExperimentRunner;
class HandbookPage;
class PocketCubePage;
class WorkbenchPage;
class TypeSemanticsLessonPage;
struct ExperimentSelection;

// 顶层窗口只负责导航、页面切换、跨模块事件与模块生命周期。代码页、
// 手册、实践页、对话框和实验执行的内部状态分别由功能模块拥有。
class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    ~MainWindow() override;

    // 应用菜单模型：macOS 上系统标准菜单栏接管它，其他平台绑定给窗口内
    // 的 PopoverMenuBar；两条路径共享同一份模型和同一组 win.* 动作，
    // 见 menu_bar_platform.h。
    Glib::RefPtr<Gio::MenuModel> menu_model() const { return m_menu_model; }
    // 供 Athena（Gtk::Application）接到 macOS 原生应用菜单模板的
    // "关于"/"偏好设置" 两个约定动作，见 athena.cc。
    void show_about_dialog();
    void show_settings_dialog();

private:
    void load_chapter_metadata();
    void open_learning_store();
    void setup_menu();
    void build_home_graph();
    // 首页上 apps/ 里那些独立学习应用的入口（ADR 0032）。
    void build_home_apps();
    void launch_home_app(const struct ExternalApp& app);
    void go_home();
    void enter_category(const string& category_name);
    void build_category(const string& category_name);
    void ensure_chapter_page(
        const string& category_name,
        const ChapterMeta& chapter);

    // 面包屑：分类名是可点击的链接按钮，其余层级是纯文本。
    void clear_breadcrumb();
    void show_category_breadcrumb(const string& category_name);
    void show_chapter_breadcrumb(
        const string& category_name,
        const string& trailing);

    // 分类内导航：索引页 ↔ 章节 ↔ 学习工具，统一入口。
    void navigate_to(const string& category_name, const string& page_key);
    void show_category_index(const string& category_name);
    void open_chapter(const string& category_name, const ChapterMeta& chapter);
    void open_progress_page();
    void rebuild_chapter_switcher(const string& category_name);
    Gtk::Widget* create_index_page(const string& category_name);
    const ChapterMeta* find_chapter_by_key(
        const string& category_name,
        const string& page_key) const;
    string category_title(const string& category_name) const;

    void ensure_handbook_page(const string& category_name);
    void show_handbook_page(
        const string& category_name,
        const string& jump_to_document = "");

    Gtk::Widget* create_progress_page();
    void refresh_progress_page();

    void handle_chapter_overview(const ChapterMeta& chapter);
    void show_experiment(
        const ExperimentSelection& experiment,
        bool run_immediately);
    void return_from_experiment();
    Glib::RefPtr<Gtk::Builder> get_chapter_builder(
        const string& category_name,
        const string& chapter_name);

    Glib::RefPtr<Gtk::Builder> m_main_builder;
    ContentLoader m_content_loader;
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;

    Gtk::Box* m_home_graph = nullptr;
    Gtk::Box* m_home_apps = nullptr;
    Gtk::Stack* m_root_stack = nullptr;
    Gtk::Box* m_breadcrumb_box = nullptr;
    Gtk::Button* m_home_button = nullptr;
    Gtk::MenuButton* m_chapter_switcher = nullptr;
    Glib::RefPtr<Gio::Menu> m_menu_model;
    unique_ptr<ChapterPageStack> m_pages;

    string m_current_category;
    set<string> m_loaded_chapters;

    ChapterCatalog m_catalog;
    FunctionRegistry m_function_registry;
    unique_ptr<LearningStore> m_learning_store;
    shared_ptr<atomic_bool> m_ui_alive = make_shared<atomic_bool>(true);
    unique_ptr<LearningDialogs> m_dialogs;
    unique_ptr<ExperimentRunner> m_experiment_runner;
    unique_ptr<ExperimentPage> m_experiment_page;
    unique_ptr<AboutDialog> m_about_dialog;

    string m_experiment_return_category;
    string m_experiment_return_page_key;

    // 页面对象必须比其 builder 先销毁；声明在 builder map 之后，成员逆序
    // 析构自然满足。手册页常驻 Stack，ArticleView 生命周期由对象独占。
    std::map<string, unique_ptr<CodeChapterPage>> m_code_pages;
    std::map<string, unique_ptr<PocketCubePage>> m_pocket_cube_pages;
    std::map<string, unique_ptr<HandbookPage>> m_handbook_pages;
    // 学习工作台原型：目前只有 TypeSemantics 一章用它，独立于上面几个
    // map，不影响其他章节的构建路径。
    std::map<string, unique_ptr<WorkbenchPage>> m_workbench_pages;
    std::map<string, unique_ptr<TypeSemanticsLessonPage>>
        m_type_semantics_lesson_pages;
};
