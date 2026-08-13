#pragma once

#include <gtkmm.h>
#include <string>
#include <map>
#include <vector>

using std::string;
using std::vector;

// 章节元数据，运行时从 chapters.json 加载
struct ChapterMeta {
    string id;              // 唯一标识，如 "pointers_references"
    int order;              // 界面排序序号
    string title;           // "指针与引用"
    string category;        // "cpp" | "ds_algo" | "design_patterns"
    string resource_path;   // GResource 路径，如 "/app/chapters/welcome.ui"
    string widget_name;     // 定制布局根控件名，如 "welcome_page"（从 blp 文件名派生）
    vector<string> subchapters;  // 子章节标题列表（合并章节的内容）
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

    // Builder 缓存
    Glib::RefPtr<Gtk::Builder> get_chapter_builder(const string& category, const string& id);

    // UI 构建器
    Glib::RefPtr<Gtk::Builder> m_main_builder;
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;

    // 主要 UI 组件
    Gtk::Box* m_category_sidebar;      // 左侧分类导航
    Gtk::Stack* m_chapter_stack;        // 章节内容栈
    Gtk::FlowBox* m_chapter_tab_box;    // 章节标签容器（FlowBox 自动换行）

    // 分类按钮（用于互斥分组）
    vector<Gtk::ToggleButton*> m_category_buttons;

    // 章节标签按钮（当前分类，用于互斥分组）
    vector<Gtk::ToggleButton*> m_tab_buttons;

    // 当前状态
    string m_current_category;
    string m_current_chapter;
    std::set<string> m_active_page_names;  // 章节栈中的页面名（用于清理）
    std::set<string> m_loaded_chapters;    // 已初始化信号的章节 ID

    // 分类定义
    vector<CategoryInfo> m_categories = {
        {"cpp", "C++",            "applications-development-symbolic"},
        {"da",  "数据结构与算法",  "applications-science-symbolic"},
        {"dp",  "设计模式",        "applications-development-symbolic"},
    };

    // 章节元数据（按 category 命名空间嵌套，id 只在 category 内唯一）
    std::map<string, std::map<string, ChapterMeta>> m_chapters;
};
