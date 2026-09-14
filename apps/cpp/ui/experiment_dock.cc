#include "experiment_dock.h"

#include "ui/source_view.h"

#include <iomanip>
#include <sstream>

using namespace std;

namespace {

string format_elapsed(double seconds) {
    ostringstream stream;
    stream << fixed << setprecision(2) << seconds << "s";
    return stream.str();
}

} // namespace

ExperimentDock::ExperimentDock(
    const ContentLoader& content_loader,
    ExperimentRunner& experiment_runner,
    GtkSourceView* source_view,
    Gtk::TextView* result_view,
    Gtk::Button* run_button,
    Gtk::Spinner* spinner,
    Gtk::Label* status_label,
    Gtk::Label* title_label,
    Gtk::Label* objective_label)
    : m_content_loader(content_loader),
      m_experiment_runner(experiment_runner),
      m_source_view(source_view),
      m_result_view(result_view),
      m_run_button(run_button),
      m_spinner(spinner),
      m_status_label(status_label),
      m_title_label(title_label),
      m_objective_label(objective_label) {
    if (m_run_button) {
        m_run_button->set_sensitive(false);
        m_run_button->signal_clicked().connect(
            [this]() { run_selected(); });
    }
    set_running(false);
}

ExperimentDock::~ExperimentDock() {
    m_alive->store(false);
    m_elapsed_timer.disconnect();
}

void ExperimentDock::show_source_file(const string& source_path) {
    display_project_source(m_source_view, m_content_loader, source_path);
}

void ExperimentDock::select(
    const ExperimentSelection& experiment, bool scroll_to_member) {
    m_selection = experiment;
    display_project_source(
        m_source_view,
        m_content_loader,
        experiment.source_path,
        scroll_to_member ? experiment.member_name : "");

    // 工作台的实验坞默认隐藏。第一次展开时，GtkTextView 即使已经收到
    // map 信号，也可能还没有非零的最终分配；立即滚动只能完成高亮、无法
    // 把目标行带进视口。等一帧布局结束后，对仍在选中的实验补一次定位。
    if (scroll_to_member) {
        auto alive = m_alive;
        Glib::signal_timeout().connect_once(
            [this, alive, experiment]() {
                if (!alive->load() || !m_selection ||
                    m_selection->function_id != experiment.function_id) {
                    return;
                }
                scroll_source_to_cursor(m_source_view);
            },
            80);
    }
    if (m_title_label) {
        m_title_label->set_text(experiment.title);
    }
    if (m_objective_label) {
        m_objective_label->set_text(experiment.description);
    }
    if (m_result_view) {
        m_result_view->get_buffer()->set_text("尚未运行。先预测结果，再点击运行验证。");
    }
    if (m_run_button) {
        m_run_button->set_sensitive(!m_experiment_runner.running());
    }
}

bool ExperimentDock::run_selected() {
    if (!m_selection) {
        return false;
    }

    const ExperimentSelection requested = *m_selection;
    auto alive = m_alive;
    const bool started = m_experiment_runner.start(
        {.function_id = requested.function_id},
        [this, alive, function_id = requested.function_id](
            const ExperimentResult& result) {
            if (!alive->load()) {
                return;
            }
            m_elapsed_timer.disconnect();
            set_running(false);

            // 用户可能在后台实验结束前切到了另一个实验；旧结果不应覆盖
            // 当前实验的结果区。
            if (m_selection && m_selection->function_id == function_id &&
                m_result_view) {
                m_result_view->get_buffer()->set_text(result.display_output);
            }
        });
    if (!started) {
        return false;
    }

    if (m_result_view) {
        m_result_view->get_buffer()->set_text("运行中…");
    }
    m_started_at = chrono::steady_clock::now();
    set_running(true);

    m_elapsed_timer.disconnect();
    m_elapsed_timer = Glib::signal_timeout().connect(
        [this, alive]() -> bool {
            if (!alive->load() || !m_status_label) {
                return false;
            }
            const auto elapsed = chrono::duration<double>(
                chrono::steady_clock::now() - m_started_at);
            m_status_label->set_text(
                "运行中 · " + format_elapsed(elapsed.count()));
            return true;
        },
        200);
    return true;
}

bool ExperimentDock::has_selection() const {
    return m_selection.has_value();
}

void ExperimentDock::set_running(bool running) {
    if (m_spinner) {
        m_spinner->set_visible(running);
        m_spinner->set_spinning(running);
    }
    if (m_status_label) {
        m_status_label->set_visible(running);
        if (running) {
            m_status_label->set_text("运行中 · 0.00s");
        }
    }
    if (m_run_button) {
        m_run_button->set_sensitive(!running && m_selection.has_value());
    }
}
