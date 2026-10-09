#pragma once

#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"
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
        const FunctionRegistry& function_registry,
        LearningStore* learning_store,
        LearningDialogs& dialogs,
        function<void(const ExperimentSelection&, bool)> on_experiment_requested,
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
    // 读取某个知识点的熟练度（0-5）；没有学习库或读失败时按 0 处理。
    int mastery_of(const string& function_id) const;
    // 把列表滚动并选中到同章的某个知识点，供先修链接跳转。
    void focus_topic(const string& function_id);

    ChapterMeta m_chapter;
    Glib::RefPtr<Gtk::Builder> m_builder;
    const FunctionRegistry& m_function_registry;
    LearningStore* m_learning_store = nullptr;
    LearningDialogs& m_dialogs;
    function<void(const ExperimentSelection&, bool)> m_on_experiment_requested;
    function<void()> m_on_progress_changed;

    Gtk::ListBox* m_topics_list = nullptr;
    // function_id -> 列表行，先修链接据此定位；populate_topic_list 时建立。
    map<string, Gtk::ListBoxRow*> m_rows_by_function_id;
    Gtk::Label* m_knowledge_description_label = nullptr;
    Gtk::Label* m_header_title_label = nullptr;
    Gtk::Label* m_header_description_label = nullptr;
    Gtk::Image* m_header_icon = nullptr;
    shared_ptr<atomic_bool> m_alive = make_shared<atomic_bool>(true);
};
