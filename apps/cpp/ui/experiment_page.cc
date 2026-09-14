#include "experiment_page.h"

#include <stdexcept>
#include <utility>

using namespace std;

ExperimentPage::ExperimentPage(
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    ExperimentRunner& experiment_runner,
    function<void()> on_return_requested)
    : m_experiment_runner(experiment_runner) {
    auto* source_view = GTK_SOURCE_VIEW(
        gtk_builder_get_object(builder->gobj(), "experiment_source_view"));
    auto* result_view =
        builder->get_widget<Gtk::TextView>("experiment_result_view");
    auto* run_button =
        builder->get_widget<Gtk::Button>("experiment_run_button");
    auto* spinner =
        builder->get_widget<Gtk::Spinner>("experiment_spinner");
    auto* status_label =
        builder->get_widget<Gtk::Label>("experiment_status_label");
    auto* title_label =
        builder->get_widget<Gtk::Label>("experiment_title_label");
    auto* objective_label =
        builder->get_widget<Gtk::Label>("experiment_objective_label");
    auto* back_button =
        builder->get_widget<Gtk::Button>("experiment_back_button");
    m_workspace_paned =
        builder->get_widget<Gtk::Paned>("experiment_workspace_paned");

    if (!source_view || !result_view || !run_button || !spinner
        || !status_label || !title_label || !objective_label || !back_button
        || !m_workspace_paned) {
        throw runtime_error("Failed to load the focused experiment page");
    }

    back_button->signal_clicked().connect(std::move(on_return_requested));
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

void ExperimentPage::show(
    const ExperimentSelection& experiment, bool run_immediately) {
    initialize_balanced_split();
    // 一个实验正在运行时不允许切换选择，避免旧任务结果写进新知识点。
    if (!m_experiment_runner.running()) {
        m_dock->select(experiment);
        m_selected_function_id = experiment.function_id;
    }
    if (run_immediately && !m_experiment_runner.running()
        && m_selected_function_id == experiment.function_id) {
        m_dock->run_selected();
    }
}

void ExperimentPage::initialize_balanced_split() {
    if (m_has_initialized_split || !m_workspace_paned) {
        return;
    }

    // show_experiment() 刚把 root Stack 切到实验页时，Paned 可能还没有实际
    // 宽度。空闲回调在本轮布局后读取可用宽度，确保首次展示就是 50 / 50；
    // 后续不再干预用户手动拖动的比例。
    Glib::signal_idle().connect_once([this]() {
        if (!m_workspace_paned) {
            return;
        }
        const int width = m_workspace_paned->get_allocated_width();
        if (width <= 0) {
            return;
        }
        m_workspace_paned->set_position(width / 2);
        m_has_initialized_split = true;
    });
}
