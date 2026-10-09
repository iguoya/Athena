#pragma once

#include "content/content_loader.h"
#include "services/case_workspace.h"
#include "services/experiment_runner.h"
#include "ui/case_dock.h"
#include "ui/experiment_dock.h"

#include <gtkmm.h>

#include <atomic>
#include <functional>
#include <memory>
#include <string>

using namespace std;

// 主窗口内的专注实验页。Blueprint 拥有静态控件树，ExperimentDock 负责
// 当前源码、执行状态和结果；页面只接线“返回原文”以及选择切换。
class ExperimentPage final {
public:
    ExperimentPage(
        const Glib::RefPtr<Gtk::Builder>& builder,
        const ContentLoader& content_loader,
        ExperimentRunner& experiment_runner,
        shared_ptr<atomic_bool> ui_alive,
        function<void()> on_return_requested);

    void show(const ExperimentSelection& experiment, bool run_immediately);

private:
    void initialize_balanced_split();
    void initialize_case_split();

    ExperimentRunner& m_experiment_runner;
    Gtk::Paned* m_workspace_paned = nullptr;
    Gtk::Paned* m_case_paned = nullptr;
    Gtk::Notebook* m_notebook = nullptr;
    unique_ptr<ExperimentDock> m_dock;
    unique_ptr<CaseDock> m_case_dock;
    string m_selected_function_id;
    bool m_has_initialized_split = false;
    bool m_has_initialized_case_split = false;
};
