#pragma once

#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"
#include "render/article_view.h"
#include "content/content_loader.h"
#include "storage/learning_store.h"
#include "ui/learning_dialogs.h"

#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <atomic>
#include <functional>
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
    void ensure_chapter_page(
        const string& category_name,
        const ChapterMeta& chapter);
    // 手册按分类各自独立，每个分类一部，作为该分类标签行里的合成标签页；
    // 没有跨分类的全局手册入口（见 ADR 0012）。
    void ensure_handbook_page(const string& category_name);
    void show_handbook_page(
        const string& category_name,
        const string& jump_to_document = "");
    void append_handbook_tab(const string& category_name);
    // cpp 分类“欢迎页面”后面的合成学习进度标签页：它不来自
    // athena.json，由 build_chapter_tabs() 在欢迎页之后手工插入。页面
    // 初次进入、AI 成绩保存成功和再次激活标签时都从 LearningStore 重建，
    // 避免统计停留在进入分类时的旧快照。
    Gtk::Widget* create_progress_page();
    void append_progress_tab();
    void refresh_progress_page();
    void initialize_code_page(
        const string& category_name,
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder);
    // “应用实践”类章节的专属布局（practice_cube.blp 等），只有标题/
    // 简介/本章总纲和一个“运行”按钮，没有标准教学页那套知识点列表；
    // 目前只有 2 阶魔方一个章节在用，暂时按“只有一个知识点”简化处理，
    // 以后同类章节多了再抽象成通用逻辑。
    void initialize_practice_page(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder);
    void populate_topic_list(
        const ChapterMeta& chapter,
        GtkSourceView* source_view,
        Gtk::TextView* result_view,
        Gtk::ListBox& topics_list,
        Gtk::Label* knowledge_description_label,
        Gtk::Spinner* experiment_spinner,
        Gtk::Label* experiment_status_label,
        Gtk::Label* header_title_label,
        Gtk::Label* header_description_label,
        Gtk::Image* header_icon);
    void open_learning_store();
    // 惰性创建、常驻复用：内容是静态的（不像运行历史/AI 自测每次点击都要
    // 拿新数据），不需要每次点击都新建再销毁那一整套。
    void show_about_dialog();
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
    // MainWindow 继承自 Gtk::Widget 一系，其自带名为 map 的控件生命周期
    // 成员，类作用域内裸写 map 会撞名，这里必须显式 std::map。
    std::map<string, Glib::RefPtr<Gtk::Builder>> m_chapter_builders;
    std::map<string, unique_ptr<ArticleView>> m_article_views;

    Gtk::Box* m_category_sidebar = nullptr;
    Gtk::Stack* m_chapter_stack = nullptr;
    Gtk::FlowBox* m_chapter_tab_box = nullptr;

    vector<Gtk::ToggleButton*> m_category_buttons;
    vector<Gtk::ToggleButton*> m_tab_buttons;
    // 分类名 -> 该分类手册标签按钮；按钮随标签栏重建而重建，指针在
    // build_chapter_tabs() 里同步作废。
    std::map<string, Gtk::ToggleButton*> m_handbook_tab_buttons;

    string m_current_category;
    string m_current_chapter;
    set<string> m_active_page_names;
    set<string> m_loaded_chapters;
    // 手册页面每个分类懒构建一次，之后常驻 Stack（不进
    // m_active_page_names，否则切分类会连控件带 WebView 一起销毁）。
    set<string> m_handbook_built_categories;
    // 分类名 -> （文档路径 -> 该文档在本分类手册里的起始锚点）。
    std::map<string, std::map<string, string>> m_handbook_anchors_by_category;

    ChapterCatalog m_catalog;
    FunctionRegistry m_function_registry;
    unique_ptr<LearningStore> m_learning_store;
    // 设置、运行历史和 AI 自测对话框；在 open_learning_store() 之后建立，
    // 之后与窗口同生命周期。窗口只负责在按钮回调里把当前知识点交给它，
    // 不再自己装配对话框控件树（ADR 0014 第 3 步）。
    unique_ptr<LearningDialogs> m_dialogs;
    // make_managed 持有；显式 set_hide_on_close(true) 后关闭按钮只隐藏不
    // 销毁，指针在窗口生命周期内始终有效，可以放心惰性创建后反复 present()。
    Gtk::AboutDialog* m_about_dialog = nullptr;

    // 实验执行状态：m_experiment_running 只在主线程读写；
    // m_ui_alive 在窗口析构时置 false，供工作线程的回传回调判断控件是否仍然可用。
    // 工作线程在完成回传时和窗口析构时 join。
    shared_ptr<atomic_bool> m_ui_alive = make_shared<atomic_bool>(true);
    bool m_experiment_running = false;
    sigc::connection m_elapsed_timer;
    thread m_experiment_thread;
};
