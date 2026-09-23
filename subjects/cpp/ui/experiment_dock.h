#pragma once

#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "services/experiment_runner.h"

#include <gtkmm.h>
#include <gtksourceview/gtksource.h>

#include <atomic>
#include <chrono>
#include <memory>
#include <optional>
#include <string>

using namespace std;

// 一个实验在界面层所需的最小信息。它只描述“验证什么、运行什么”，
// 不携带章节、文档锚点或列表行等页面状态。
struct ExperimentSelection {
    string function_id;
    string title;
    string description;
    string source_path;
    string member_name;
    // 这个知识点挂的骨架案例（ADR 0053），可以为空。实验页据此决定
    // 要不要显示「动手实验」那一页。
    vector<LabSpec> labs;
};

// ExperimentDock 不拥有控件；同一套控制逻辑可以接到代码章节页或学习
// 工作台的不同 Blueprint 上。页面仍负责“选哪个实验”，实验坞只负责
// 展示真实源码、运行当前实验和呈现结果。
class ExperimentDock final {
public:
    ExperimentDock(
        const ContentLoader& content_loader,
        ExperimentRunner& experiment_runner,
        GtkSourceView* source_view,
        Gtk::TextView* result_view,
        Gtk::Button* run_button = nullptr,
        Gtk::Spinner* spinner = nullptr,
        Gtk::Label* status_label = nullptr,
        Gtk::Label* title_label = nullptr,
        Gtk::Label* objective_label = nullptr);
    ~ExperimentDock();

    ExperimentDock(const ExperimentDock&) = delete;
    ExperimentDock& operator=(const ExperimentDock&) = delete;

    void show_source_file(const string& source_path);
    void select(const ExperimentSelection& experiment, bool scroll_to_member = true);
    bool run_selected();
    bool has_selection() const;

private:
    void set_running(bool running);

    const ContentLoader& m_content_loader;
    ExperimentRunner& m_experiment_runner;
    GtkSourceView* m_source_view = nullptr;
    Gtk::TextView* m_result_view = nullptr;
    Gtk::Button* m_run_button = nullptr;
    Gtk::Spinner* m_spinner = nullptr;
    Gtk::Label* m_status_label = nullptr;
    Gtk::Label* m_title_label = nullptr;
    Gtk::Label* m_objective_label = nullptr;

    optional<ExperimentSelection> m_selection;
    shared_ptr<atomic_bool> m_alive = make_shared<atomic_bool>(true);
    sigc::connection m_elapsed_timer;
    chrono::steady_clock::time_point m_started_at;
};
