#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"
#include "services/experiment_runner.h"
#include "storage/learning_store.h"
#include "ui/dialog_topic.h"
#include "ui/learning_dialogs.h"

#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <atomic>
#include <chrono>
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
        string description;
        string source_path;
        string member_name;
        string title;
        string function_id;
        IconSpec icon;
    };

    void populate_topic_list();
    void start_experiment(const TopicSelection& topic);

    ChapterMeta m_chapter;
    Glib::RefPtr<Gtk::Builder> m_builder;
    const ContentLoader& m_content_loader;
    const FunctionRegistry& m_function_registry;
    LearningStore* m_learning_store = nullptr;
    LearningDialogs& m_dialogs;
    ExperimentRunner& m_experiment_runner;
    function<void()> m_on_progress_changed;

    GtkSourceView* m_source_view = nullptr;
    Gtk::TextView* m_result_view = nullptr;
    Gtk::ListBox* m_topics_list = nullptr;
    Gtk::Label* m_knowledge_description_label = nullptr;
    Gtk::Spinner* m_experiment_spinner = nullptr;
    Gtk::Label* m_experiment_status_label = nullptr;
    Gtk::Label* m_header_title_label = nullptr;
    Gtk::Label* m_header_description_label = nullptr;
    Gtk::Image* m_header_icon = nullptr;

    shared_ptr<atomic_bool> m_alive = make_shared<atomic_bool>(true);
    sigc::connection m_elapsed_timer;
    chrono::steady_clock::time_point m_experiment_started;
};
