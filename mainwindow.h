#pragma once

#include "article_view.h"

#include <gtkmm.h>

#include <map>
#include <set>
#include <string>
#include <vector>

using namespace std;

struct IconSpec {
    string type;
    string name;
    string path;
};

struct SubChapter {
    string name;
    string title;
    string description;
    string group;
    string source;
    IconSpec icon;
};

struct ChapterGroup {
    string name;
    string title;
    string description;
    string source;
    IconSpec icon;
};

struct ChapterMeta {
    string name;
    string title;
    string description;
    string category;
    string content;
    string document;
    string blueprint;
    string resource_path;
    string widget_name;
    string source;
    IconSpec icon;
    vector<ChapterGroup> groups;
    vector<SubChapter> subchapters;
};

struct CategoryInfo {
    string name;
    string title;
    string description;
    IconSpec icon;
};

class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    virtual ~MainWindow() = default;

private:
    void load_chapter_metadata();
    void setup_category_sidebar();
    void on_category_selected(const string& category_name);
    void build_chapter_tabs(const string& category_name);

    Glib::RefPtr<Gtk::Builder> get_chapter_builder(
        const string& category_name,
        const string& chapter_name);
    const ChapterMeta* find_chapter(
        const string& category_name,
        const string& chapter_name) const;

    void configure_image(Gtk::Image& image, const IconSpec& icon, int pixel_size) const;
    Gtk::Image* create_icon(const IconSpec& icon, int pixel_size) const;

    Glib::RefPtr<Gtk::Builder> m_main_builder;
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;
    std::map<string, std::unique_ptr<athena::ArticleView>> m_article_views;

    Gtk::Box* m_category_sidebar = nullptr;
    Gtk::Stack* m_chapter_stack = nullptr;
    Gtk::FlowBox* m_chapter_tab_box = nullptr;

    vector<Gtk::ToggleButton*> m_category_buttons;
    vector<Gtk::ToggleButton*> m_tab_buttons;

    string m_current_category;
    string m_current_chapter;
    set<string> m_active_page_names;
    set<string> m_loaded_chapters;

    string m_default_chapter_content;
    string m_default_code_chapter_blueprint;
    string m_default_article_chapter_blueprint;
    IconSpec m_default_chapter_icon;
    IconSpec m_default_subchapter_icon;

    vector<CategoryInfo> m_categories;
    std::map<string, vector<ChapterMeta>> m_chapters;
};
