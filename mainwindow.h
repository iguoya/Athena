#pragma once

#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"
#include "render/article_view.h"
#include "content/content_loader.h"

#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <set>

using namespace std;

class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    virtual ~MainWindow() = default;

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
        Gtk::Label* knowledge_description_label);

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
};
