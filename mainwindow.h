#pragma once

#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"
#include "render/article_view.h"
#include "content/content_loader.h"
#include "storage/learning_store.h"

#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <atomic>
#include <memory>
#include <set>
#include <thread>

using namespace std;

class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    ~MainWindow() override;

private:
    void load_chapter_metadata();
    void setup_category_sidebar();
    void on_category_selected(const string& category_name);
    void build_chapter_tabs(const string& category_name);
    bool initialize_article_page(
        const string& page_key,
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder);
    void initialize_code_page(
        const string& category_name,
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder);
    void populate_topic_list(
        const string& category_name,
        const ChapterMeta& chapter,
        GtkSourceView* source_view,
        Gtk::TextView* result_view,
        Gtk::ListBox& topics_list,
        Gtk::Label* knowledge_description_label,
        Gtk::Spinner* experiment_spinner,
        Gtk::Label* experiment_status_label);
    void open_learning_store();
    void show_note_dialog(const string& function_id, const string& topic_title);
    void show_history_dialog(
        const string& function_id,
        const string& source_path,
        const string& member_name,
        const string& topic_title);
    void start_experiment(
        const string& function_id,
        const string& source_path,
        const string& member_name,
        Gtk::TextView& result_view,
        Gtk::Spinner* experiment_spinner,
        Gtk::Label* experiment_status_label);

    Glib::RefPtr<Gtk::Builder> get_chapter_builder(
        const string& category_name,
        const string& chapter_name);
    void configure_image(Gtk::Image& image, const IconSpec& icon, int pixel_size) const;
    Gtk::Image* create_icon(const IconSpec& icon, int pixel_size) const;

    Glib::RefPtr<Gtk::Builder> m_main_builder;
    ContentLoader m_content_loader;
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;
    std::map<string, std::unique_ptr<ArticleView>> m_article_views;

    Gtk::Box* m_category_sidebar = nullptr;
    Gtk::Stack* m_chapter_stack = nullptr;
    Gtk::FlowBox* m_chapter_tab_box = nullptr;

    vector<Gtk::ToggleButton*> m_category_buttons;
    vector<Gtk::ToggleButton*> m_tab_buttons;

    string m_current_category;
    string m_current_chapter;
    set<string> m_active_page_names;
    set<string> m_loaded_chapters;

    ChapterCatalog m_catalog;
    FunctionRegistry m_function_registry;
    unique_ptr<LearningStore> m_learning_store;

    // 实验执行状态：m_experiment_running 只在主线程读写；
    // m_ui_alive 在窗口析构时置 false，供工作线程的回传回调判断控件是否仍然可用。
    // 工作线程在完成回传时和窗口析构时 join。
    std::shared_ptr<std::atomic_bool> m_ui_alive =
        std::make_shared<std::atomic_bool>(true);
    bool m_experiment_running = false;
    sigc::connection m_elapsed_timer;
    std::thread m_experiment_thread;
};
