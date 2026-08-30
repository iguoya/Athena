#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "render/article_view.h"
#include "services/experiment_runner.h"

#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <atomic>
#include <map>
#include <memory>
#include <string>
#include <utility>

using namespace std;

// 学习工作台原型：手册主导、实验坞从属，宽度比例 2:1（对应
// docs/LEARNING_WORKSPACE_BENCH.md 的图 1）。左侧渲染本章 handbook 文档
// 的真实正文，右侧是知识点列表 + 真实源码 + 运行结果。两侧双向联动：
// 右侧列表驱动左侧文档滚到对应小节；文档里配了 teaches 的小节末尾会在
// 渲染期挂载一张"动手验证"卡片，点击驱动右侧选中并高亮对应知识点。
//
// 目前只有一章（TypeSemantics）用它，独立于 CodeChapterPage 和
// HandbookPage：不共享控件树、不改动它们的实现，删掉这个类不影响其他
// 任何章节。
class WorkbenchPage final {
public:
    WorkbenchPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        const ContentLoader& content_loader,
        ExperimentRunner& experiment_runner,
        Gtk::Window& parent);
    ~WorkbenchPage();

    WorkbenchPage(const WorkbenchPage&) = delete;
    WorkbenchPage& operator=(const WorkbenchPage&) = delete;

private:
    void load_article();
    void populate_topic_list();
    // scroll_source_view=false 只更新状态、列表高亮和手册滚动（手册的
    // ArticleView 自己会缓存加载完成前的跳转请求），不去滚动源码框——
    // 源码框的滚动依赖控件已经完成过一次真实布局分配，页面刚构造、
    // 还没被map到屏幕上时调用没有意义，只会滚到一个跟目标行无关的
    // 位置。构造期间的初始自动选中传 false，用户真实点击时用默认值。
    void select_subchapter(
        Gtk::ListBoxRow& row,
        const SubChapter& subchapter,
        bool scroll_source_view = true);
    // 文档里"动手验证"卡片被点击时的回调；knowledge_id 就是
    // subchapter.function_id。查不到对应知识点时静默忽略。
    void select_by_knowledge_id(const string& knowledge_id);
    void run_current_experiment();

    const ChapterMeta& m_chapter;
    const ContentLoader& m_content_loader;
    ExperimentRunner& m_experiment_runner;

    GtkSourceView* m_source_view = nullptr;
    Gtk::ListBox* m_topics_list = nullptr;
    Gtk::ListBoxRow* m_active_row = nullptr;
    Gtk::Button* m_run_button = nullptr;
    Gtk::TextView* m_result_view = nullptr;

    unique_ptr<ArticleView> m_article_view;
    // 知识点声明的 teaches.heading 反查这份文档实际解析出的锚点——
    // 找不到就不跳转，不阻断页面其余部分工作。
    map<string, string> m_anchor_by_heading;
    // 供文档里渲染期挂载的"动手验证"卡片点击后反查：function_id ->
    // 对应的列表行 + 知识点数据，用于双向联动的"文档 → 实验坞"方向。
    map<string, pair<Gtk::ListBoxRow*, const SubChapter*>> m_topic_by_function_id;

    string m_current_function_id;
    string m_current_source_path;
    string m_current_member_name;

    shared_ptr<atomic_bool> m_alive = make_shared<atomic_bool>(true);
};
