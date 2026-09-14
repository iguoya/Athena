#pragma once

#include "content/content_loader.h"
#include "services/experiment_runner.h"
#include "ui/experiment_dock.h"

#include <gtkmm.h>

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
        function<void()> on_return_requested);

    void show(const ExperimentSelection& experiment, bool run_immediately);

private:
    void initialize_balanced_split();

    ExperimentRunner& m_experiment_runner;
    Gtk::Paned* m_workspace_paned = nullptr;
    unique_ptr<ExperimentDock> m_dock;
    string m_selected_function_id;
    bool m_has_initialized_split = false;
};
