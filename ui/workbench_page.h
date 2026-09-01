#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "render/article_view.h"
#include "ui/experiment_dock.h"

#include <gtkmm.h>

#include <functional>
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
        Gtk::Window& parent,
        function<void(const ExperimentSelection&, bool)> on_experiment_requested);
    ~WorkbenchPage();

    WorkbenchPage(const WorkbenchPage&) = delete;
    WorkbenchPage& operator=(const WorkbenchPage&) = delete;

private:
    void load_article();
    void select_by_knowledge_id(const string& knowledge_id);

    const ChapterMeta& m_chapter;
    const ContentLoader& m_content_loader;
    function<void(const ExperimentSelection&, bool)> m_on_experiment_requested;

    unique_ptr<ArticleView> m_article_view;
    map<string, const SubChapter*> m_topic_by_function_id;
};
