#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "render/article_view.h"
#include "ui/experiment_dock.h"

#include <gtkmm.h>

#include <map>
#include <memory>
#include <string>

using namespace std;

// 文档主导的学习工作台。页面只协调“文档中的实验入口 -> 当前实验坞”；
// 源码展示和运行状态由可复用的 ExperimentDock 负责。
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
    void select_by_knowledge_id(const string& knowledge_id);
    void update_section_position(const SubChapter& selected);

    const ChapterMeta& m_chapter;
    const ContentLoader& m_content_loader;

    unique_ptr<ArticleView> m_article_view;
    unique_ptr<ExperimentDock> m_experiment_dock;
    map<string, const SubChapter*> m_topic_by_function_id;

    Gtk::Box* m_dock_panel = nullptr;
    Gtk::Label* m_experiment_count_label = nullptr;
};
