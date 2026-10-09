#include "experiment_page.h"

#include <stdexcept>
#include <utility>

using namespace std;

ExperimentPage::ExperimentPage(
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    ExperimentRunner& experiment_runner,
    shared_ptr<atomic_bool> ui_alive,
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
    m_case_paned = builder->get_widget<Gtk::Paned>("case_workspace_paned");
    m_notebook = builder->get_widget<Gtk::Notebook>("experiment_notebook");

    if (!source_view || !result_view || !run_button || !spinner
        || !status_label || !title_label || !objective_label || !back_button
        || !m_workspace_paned || !m_case_paned || !m_notebook) {
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
    m_case_dock = make_unique<CaseDock>(
        builder, CaseWorkspace(CaseWorkspace::default_root()), std::move(ui_alive));

    // 动手实验那一页初始不可见，Paned 此时没有宽度，show() 里设不了分栏。
    // 等它第一次真正显示出来再设。
    m_notebook->signal_switch_page().connect(
        [this](Gtk::Widget*, guint) { initialize_case_split(); });
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

    // 没挂案例的知识点不显示「动手实验」页——Notebook 的标签跟着子控件
    // 的可见性走，隐藏 Paned 那一页整个就不出现。
    const bool has_case = !experiment.labs.empty();
    m_case_paned->set_visible(has_case);
    if (has_case) {
        m_case_dock->show(experiment.labs.front());
    }
}

void ExperimentPage::initialize_case_split() {
    if (m_has_initialized_case_split || !m_case_paned) {
        return;
    }
    Glib::signal_idle().connect_once([this]() {
        if (!m_case_paned) {
            return;
        }
        const int width = m_case_paned->get_allocated_width();
        if (width <= 0) {
            return;
        }
        m_case_paned->set_position(width / 2);
        m_has_initialized_case_split = true;
    });
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
