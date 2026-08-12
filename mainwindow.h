#pragma once

#include <gtkmm.h>
#include <string>
#include <map>
#include <vector>

using std::string;
using std::vector;

// 章节元数据，运行时从 chapters.json 加载
struct ChapterMeta {
    string id;
    string title;
    string resource_path;  // GResource 路径，如 "/app/chapters/welcome.ui"
};

class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    virtual ~MainWindow() = default;

private:
    // 加载章节元数据
    void load_chapter_metadata();

    // 事件处理函数
    void on_menu_row_activated(Gtk::ListBoxRow* row);
    void load_chapter(const string& chapter_name);
    void setup_window_controls();

    // 章节特定的初始化
    void initialize_basic_syntax_chapter(const Glib::RefPtr<Gtk::Builder>& builder);
    void initialize_functions_chapter(const Glib::RefPtr<Gtk::Builder>& builder);

    // UI 构建器
    Glib::RefPtr<Gtk::Builder> m_main_builder;
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;

    // 主要 UI 组件
    Gtk::ListBox* m_menu_list;
    Gtk::Box* m_content_container;
    Gtk::Label* m_content_title;

    // 当前页面状态
    string m_current_chapter;
    Gtk::Widget* m_current_widget;

    // 新增：用于跟踪和控制欢迎页面的状态和控件**
    Gtk::Box* m_welcome_content_box;
    bool m_is_welcome_page_shown = true;

    // 章节元数据（运行时从 chapters.json 加载，替代硬编码 map）
    std::map<string, ChapterMeta> m_chapters;
};
