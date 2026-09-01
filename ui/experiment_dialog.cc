#include "experiment_dialog.h"

#include <stdexcept>

using namespace std;

ExperimentDialog::ExperimentDialog(
    Gtk::Window& parent,
    const ContentLoader& content_loader,
    ExperimentRunner& experiment_runner)
    : m_parent(parent), m_experiment_runner(experiment_runner) {
    m_builder = Gtk::Builder::create_from_resource("/app/experiment_dialog.ui");
    m_window = m_builder->get_widget<Gtk::Window>("experiment_dialog_window");
    auto* source_view = GTK_SOURCE_VIEW(
        gtk_builder_get_object(m_builder->gobj(), "experiment_source_view"));
    auto* result_view =
        m_builder->get_widget<Gtk::TextView>("experiment_result_view");
    auto* run_button =
        m_builder->get_widget<Gtk::Button>("experiment_run_button");
    auto* spinner =
        m_builder->get_widget<Gtk::Spinner>("experiment_spinner");
    auto* status_label =
        m_builder->get_widget<Gtk::Label>("experiment_status_label");
    auto* title_label =
        m_builder->get_widget<Gtk::Label>("experiment_title_label");
    auto* objective_label =
        m_builder->get_widget<Gtk::Label>("experiment_objective_label");

    if (!m_window || !source_view || !result_view || !run_button || !spinner
        || !status_label || !title_label || !objective_label) {
        throw runtime_error("Failed to load the experiment dialog widget tree");
    }

    m_window->set_transient_for(m_parent);
    // 模态：运行实验是"专注做一下"的活动，期间不需要同时操作主窗口；
    // 后续 AI 讲解 / AI 自测按钮要挂进这个窗口，它们本身也是模态对话框，
    // 统一成模态层级更清晰。见 ADR 0022 的修订记录。
    m_window->set_modal(true);
    m_window->set_hide_on_close(true);
    if (auto application = m_parent.get_application()) {
        m_window->set_application(application);
    }

    m_dock = make_unique<ExperimentDock>(
        content_loader,
        experiment_runner,
        source_view,
        result_view,
        run_button,
        spinner,
        status_label,
        title_label,
        objective_label);
}

void ExperimentDialog::present(
    const ExperimentSelection& experiment, bool run_immediately) {
    // 同一时刻只允许一个实验运行。运行期间再次从章节页或文档入口请求
    // 另一个知识点时，只把已有实验窗口带到前台，不用新选择覆盖正在运行
    // 的源码、状态和最终结果。
    if (!m_experiment_runner.running()) {
        m_dock->select(experiment);
        m_selected_function_id = experiment.function_id;
    }

    m_window->present();
    if (run_immediately && !m_experiment_runner.running()
        && m_selected_function_id == experiment.function_id) {
        m_dock->run_selected();
    }
}
