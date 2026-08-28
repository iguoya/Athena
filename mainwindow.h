#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
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
class ChapterNavStrip;
class CodeChapterPage;
class ExperimentRunner;
class HandbookPage;
class PocketCubePage;

// 顶层窗口只负责导航、页面切换、跨模块事件与模块生命周期。代码页、
// 手册、实践页、对话框和实验执行的内部状态分别由功能模块拥有。
class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    ~MainWindow() override;

private:
    void load_chapter_metadata();
    void open_learning_store();
    void setup_category_sidebar();
    void on_category_selected(const string& category_name);
    void build_chapter_tabs(const string& category_name);
    void ensure_chapter_page(
        const string& category_name,
        const ChapterMeta& chapter);

    void append_handbook_tab(const string& category_name);
    void ensure_handbook_page(const string& category_name);
    void show_handbook_page(
        const string& category_name,
        const string& jump_to_document = "");

    Gtk::Widget* create_progress_page();
    void append_progress_tab();
    void refresh_progress_page();

    void handle_chapter_overview(const ChapterMeta& chapter);
    Glib::RefPtr<Gtk::Builder> get_chapter_builder(
        const string& category_name,
        const string& chapter_name);

    Glib::RefPtr<Gtk::Builder> m_main_builder;
    ContentLoader m_content_loader;
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;

    Gtk::Box* m_category_sidebar = nullptr;
    vector<Gtk::ToggleButton*> m_category_buttons;
    unique_ptr<ChapterNavStrip> m_nav;

    string m_current_category;
    set<string> m_loaded_chapters;

    ChapterCatalog m_catalog;
    FunctionRegistry m_function_registry;
    unique_ptr<LearningStore> m_learning_store;
    shared_ptr<atomic_bool> m_ui_alive = make_shared<atomic_bool>(true);
    unique_ptr<LearningDialogs> m_dialogs;
    unique_ptr<ExperimentRunner> m_experiment_runner;
    unique_ptr<AboutDialog> m_about_dialog;

    // 页面对象必须比其 builder 先销毁；声明在 builder map 之后，成员逆序
    // 析构自然满足。手册页常驻 Stack，ArticleView 生命周期由对象独占。
    std::map<string, unique_ptr<CodeChapterPage>> m_code_pages;
    std::map<string, unique_ptr<PocketCubePage>> m_pocket_cube_pages;
    std::map<string, unique_ptr<HandbookPage>> m_handbook_pages;
};
