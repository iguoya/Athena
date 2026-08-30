#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"
#include "services/experiment_runner.h"
#include "storage/learning_store.h"
#include "ui/dialog_topic.h"
#include "ui/experiment_dock.h"
#include "ui/learning_dialogs.h"

#include <gtkmm.h>

#include <atomic>
#include <functional>
#include <map>
#include <memory>
#include <string>

using namespace std;

// 标准代码章节页：独占知识点控件树、统一激活路径、源码/结果显示和熟练度
// 回写。跨页行为通过回调上报；不认识 MainWindow。
class CodeChapterPage final {
public:
    CodeChapterPage(
        const ChapterMeta& chapter,
        const Glib::RefPtr<Gtk::Builder>& builder,
        const ContentLoader& content_loader,
        const FunctionRegistry& function_registry,
        LearningStore* learning_store,
        LearningDialogs& dialogs,
        ExperimentRunner& experiment_runner,
        function<void()> on_overview_requested,
        function<void()> on_progress_changed);
    ~CodeChapterPage();

    CodeChapterPage(const CodeChapterPage&) = delete;
    CodeChapterPage& operator=(const CodeChapterPage&) = delete;

private:
    struct TopicSelection {
        ExperimentSelection experiment;
        IconSpec icon;
    };

    void populate_topic_list();

    ChapterMeta m_chapter;
    Glib::RefPtr<Gtk::Builder> m_builder;
    const FunctionRegistry& m_function_registry;
    LearningStore* m_learning_store = nullptr;
    LearningDialogs& m_dialogs;
    function<void()> m_on_progress_changed;

    Gtk::ListBox* m_topics_list = nullptr;
    Gtk::Label* m_knowledge_description_label = nullptr;
    Gtk::Label* m_header_title_label = nullptr;
    Gtk::Label* m_header_description_label = nullptr;
    Gtk::Image* m_header_icon = nullptr;
    unique_ptr<ExperimentDock> m_experiment_dock;

    shared_ptr<atomic_bool> m_alive = make_shared<atomic_bool>(true);
};
