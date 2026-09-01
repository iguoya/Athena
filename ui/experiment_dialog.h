#pragma once

#include "content/content_loader.h"
#include "services/experiment_runner.h"
#include "ui/experiment_dock.h"

#include <gtkmm.h>

#include <memory>
#include <string>

using namespace std;

// 单例、非模态的实验窗口。窗口拥有 Blueprint 控件树，ExperimentDock
// 继续只负责源码定位、实验执行状态和结果呈现。
class ExperimentDialog final {
public:
    ExperimentDialog(
        Gtk::Window& parent,
        const ContentLoader& content_loader,
        ExperimentRunner& experiment_runner);

    void present(const ExperimentSelection& experiment, bool run_immediately);

private:
    Gtk::Window& m_parent;
    ExperimentRunner& m_experiment_runner;
    Glib::RefPtr<Gtk::Builder> m_builder;
    Gtk::Window* m_window = nullptr;
    unique_ptr<ExperimentDock> m_dock;
    string m_selected_function_id;
};
