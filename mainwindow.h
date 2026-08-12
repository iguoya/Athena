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
    string category;       // "cpp" | "ds_algo" | "design_patterns"
    string resource_path;  // GResource 路径，如 "/app/chapters/welcome.ui"
};

// 分类信息
struct CategoryInfo {
    string id;
    string title;
    string icon_name;
};

class MainWindow : public Gtk::ApplicationWindow {
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gtk::Builder>& builder);
    virtual ~MainWindow() = default;

private:
    // 初始化
    void load_chapter_metadata();
    void setup_category_sidebar();

    // 分类切换
    void on_category_selected(const string& category_id);
    void build_chapter_tabs(const string& category_id);

    // 章节加载
    void load_chapter(const string& chapter_name);
    void load_chapter_content(const string& chapter_name);

    // 章节特定的初始化（信号连接等）
    void initialize_basic_syntax_chapter(const Glib::RefPtr<Gtk::Builder>& builder);
    void initialize_functions_chapter(const Glib::RefPtr<Gtk::Builder>& builder);

    // Builder 缓存
    Glib::RefPtr<Gtk::Builder> get_chapter_builder(const string& chapter_name);

    // UI 构建器
    Glib::RefPtr<Gtk::Builder> m_main_builder;
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;

    // 主要 UI 组件
    Gtk::Box* m_category_sidebar;      // 左侧分类导航
    Gtk::Stack* m_chapter_stack;        // 章节内容栈
    Gtk::StackSwitcher* m_chapter_tabs; // 章节标签切换器

    // 分类按钮（用于互斥分组）
    vector<Gtk::ToggleButton*> m_category_buttons;

    // 当前状态
    string m_current_category;
    string m_current_chapter;
    std::set<string> m_active_page_names;  // 章节栈中的页面名（用于清理）
    std::set<string> m_loaded_chapters;    // 已初始化信号的章节 ID

    // 分类定义
    vector<CategoryInfo> m_categories = {
        {"cpp",              "C++",              "applications-development-symbolic"},
        {"ds_algo",          "数据结构与算法",    "applications-science-symbolic"},
        {"design_patterns",  "设计模式",          "applications-development-symbolic"},
    };

    // 章节元数据（运行时从 chapters.json 加载）
    std::map<string, ChapterMeta> m_chapters;
};
