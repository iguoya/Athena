#pragma once

#include <gtkmm.h>
#include <string>
#include <map>
using namespace std;


class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    virtual ~MainWindow() = default;

private:
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

    // 章节资源映射
    std::map<string, string> m_chapter_resources = {
        {"welcome", "/app/chapters/welcome.ui"},
        {"basic_syntax", "/app/chapters/basic_syntax.ui"},
        {"functions", "/app/chapters/functions.ui"},
        // {"control_flow", "/app/chapters/control_flow.ui"},
        // {"classes_objects", "/app/chapters/classes_objects.ui"},
        // 可以继续添加更多章节...
    };
    
    // 章节标题映射
    std::map<string, string> m_chapter_titles = {
        {"welcome", "欢迎页面"},
        {"basic_syntax", "基础语法"},
        {"functions", "函数基础"},
        // {"control_flow", "流程控制"},
        // {"classes_objects", "类与对象"},
        // 对应更多章节标题...
    };
};
