#include "ui/case_dock.h"

#include "services/case_runner.h"
#include "ui/source_view.h"

#include <glibmm/main.h>

#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <thread>
#include <utility>

using namespace std;

namespace {

string format_elapsed(double milliseconds) {
    ostringstream stream;
    stream << fixed << setprecision(2) << milliseconds / 1000.0 << "s";
    return stream.str();
}

// 把一次运行的结果摊成给人看的文本。编译诊断在前——编译不过的时候它
// 就是全部内容，而且看懂它本身就是学 C++ 的一部分（ADR 0053）。
string format_result(const CaseRunResult& result) {
    ostringstream text;
    if (!result.compiler_log.empty()) {
        text << "—— 编译器说 ——\n" << result.compiler_log;
        if (result.compiler_log.back() != '\n') {
            text << "\n";
        }
        text << "\n";
    }
    if (!result.compiled) {
        text << "编译没有通过，程序没有运行。";
        return text.str();
    }
    if (!result.stdout_text.empty()) {
        text << "—— 输出 ——\n" << result.stdout_text;
        if (result.stdout_text.back() != '\n') {
            text << "\n";
        }
    } else if (result.ran) {
        text << "—— 输出 ——\n（程序没有打印任何东西）\n";
    }
    if (!result.stderr_text.empty()) {
        text << "\n—— 标准错误 ——\n" << result.stderr_text;
    }
    if (result.ran && result.exit_status != 0) {
        text << "\n退出码 " << result.exit_status << "（非零）";
    }
    text << "\n—— 耗时 " << format_elapsed(result.duration_ms) << " ——";
    return text.str();
}

}  // namespace

// 后台线程与控件之间的共享状态。dock_alive 让 idle 回调知道工作台是不是
// 还在——析构会先置 false 再 join，之后回调只是空跑一趟。
struct CaseDock::SharedState {
    atomic_bool running{false};
    atomic_bool dock_alive{true};
    thread worker;
};

CaseDock::CaseDock(
    const Glib::RefPtr<Gtk::Builder>& builder,
    CaseWorkspace workspace,
    shared_ptr<atomic_bool> ui_alive)
    : m_workspace(std::move(workspace)),
      m_ui_alive(std::move(ui_alive)),
      m_state(make_shared<SharedState>()) {
    m_source_view = GTK_SOURCE_VIEW(
        builder->get_widget<Gtk::Widget>("case_source_view")->gobj());
    m_output_view = builder->get_widget<Gtk::TextView>("case_output_view");
    m_prompt_label = builder->get_widget<Gtk::Label>("case_prompt_label");
    m_goal_label = builder->get_widget<Gtk::Label>("case_goal_label");
    m_hint_label = builder->get_widget<Gtk::Label>("case_hint_label");
    m_file_label = builder->get_widget<Gtk::Label>("case_file_label");
    m_status_label = builder->get_widget<Gtk::Label>("case_status_label");
    m_run_button = builder->get_widget<Gtk::Button>("case_run_button");
    m_reset_button = builder->get_widget<Gtk::Button>("case_reset_button");
    m_spinner = builder->get_widget<Gtk::Spinner>("case_spinner");

    apply_cpp_highlighting(m_source_view);

    if (m_run_button) {
        m_run_button->signal_clicked().connect([this] { run(); });
    }
    if (m_reset_button) {
        m_reset_button->signal_clicked().connect([this] { confirm_reset(); });
    }
}

CaseDock::~CaseDock() {
    m_state->dock_alive.store(false);
    if (m_state->worker.joinable()) {
        m_state->worker.join();
    }
}

void CaseDock::set_source_text(const string& text) {
    auto* buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(m_source_view));
    gtk_text_buffer_set_text(buffer, text.c_str(), static_cast<int>(text.size()));
}

string CaseDock::source_text() const {
    auto* buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(m_source_view));
    GtkTextIter begin;
    GtkTextIter end;
    gtk_text_buffer_get_bounds(buffer, &begin, &end);
    char* raw = gtk_text_buffer_get_text(buffer, &begin, &end, FALSE);
    string text = raw != nullptr ? raw : "";
    g_free(raw);
    return text;
}

void CaseDock::show(const LabSpec& lab) {
    m_case_id = lab.case_id;
    m_file_name.clear();

    if (m_prompt_label) {
        m_prompt_label->set_text(lab.prompt);
    }
    if (m_goal_label) {
        m_goal_label->set_text("你要做的：" + lab.goal);
    }
    if (m_hint_label) {
        m_hint_label->set_text(lab.hint.empty() ? "" : "提示：" + lab.hint);
        m_hint_label->set_visible(!lab.hint.empty());
    }

    try {
        const vector<CaseFile> files = m_workspace.ensure(lab.case_id);
        // 一个案例通常只有 main.cpp；多文件时先认第一个。
        m_file_name = files.front().name;
        set_source_text(files.front().contents);
        if (m_file_label) {
            m_file_label->set_text(
                m_file_name + (m_workspace.modified(lab.case_id) ? "（已修改）" : ""));
        }
        if (m_output_view) {
            m_output_view->get_buffer()->set_text(
                "还没有运行。先按题目预测结果，写完再编译运行，对照你的预测。");
        }
    } catch (const exception& error) {
        m_case_id.clear();
        set_source_text("");
        if (m_output_view) {
            m_output_view->get_buffer()->set_text(
                "打不开这个实验：" + string(error.what()));
        }
    }
    if (m_run_button) {
        m_run_button->set_sensitive(!m_case_id.empty());
    }
    if (m_reset_button) {
        m_reset_button->set_sensitive(!m_case_id.empty());
    }
}

void CaseDock::save_current_edit() {
    if (m_case_id.empty() || m_file_name.empty()) {
        return;
    }
    m_workspace.save(m_case_id, m_file_name, source_text());
    if (m_file_label) {
        m_file_label->set_text(
            m_file_name + (m_workspace.modified(m_case_id) ? "（已修改）" : ""));
    }
}

void CaseDock::set_running(bool running) {
    if (m_spinner) {
        m_spinner->set_visible(running);
        running ? m_spinner->start() : m_spinner->stop();
    }
    if (m_status_label) {
        m_status_label->set_visible(running);
        if (running) {
            m_status_label->set_text("编译并运行中…");
        }
    }
    if (m_run_button) {
        m_run_button->set_sensitive(!running && !m_case_id.empty());
    }
    if (m_reset_button) {
        m_reset_button->set_sensitive(!running && !m_case_id.empty());
    }
    gtk_text_view_set_editable(GTK_TEXT_VIEW(m_source_view), !running);
}

void CaseDock::run() {
    if (m_case_id.empty() || m_state->running.load()) {
        return;
    }
    try {
        save_current_edit();
    } catch (const exception& error) {
        if (m_output_view) {
            m_output_view->get_buffer()->set_text(
                "保存失败，没有运行：" + string(error.what()));
        }
        return;
    }

    m_state->running.store(true);
    set_running(true);
    if (m_output_view) {
        m_output_view->get_buffer()->set_text("编译中…");
    }

    const string work_dir = m_workspace.directory_of(m_case_id);
    auto state = m_state;
    auto alive = m_ui_alive;
    auto* self = this;

    if (state->worker.joinable()) {
        state->worker.join();
    }
    state->worker = thread([work_dir, state, alive, self] {
        const CaseRunResult result = CaseRunner().run(work_dir);
        Glib::signal_idle().connect_once([result, state, alive, self] {
            state->running.store(false);
            if (!alive->load() || !state->dock_alive.load()) {
                return;
            }
            self->set_running(false);
            if (self->m_output_view) {
                self->m_output_view->get_buffer()->set_text(format_result(result));
            }
        });
    });
}

void CaseDock::confirm_reset() {
    if (m_case_id.empty()) {
        return;
    }
    // 重置会丢掉学员写的代码，问一句再动手。
    auto* window = dynamic_cast<Gtk::Window*>(
        m_run_button != nullptr ? m_run_button->get_root() : nullptr);
    auto dialog = Gtk::AlertDialog::create("把代码恢复成最初的骨架？");
    dialog->set_detail("你在这个实验里写的内容会丢失，这一步不能撤销。");
    dialog->set_buttons({"取消", "恢复骨架"});
    dialog->set_cancel_button(0);
    dialog->set_default_button(0);
    dialog->choose(
        *window,
        [this, dialog](const Glib::RefPtr<Gio::AsyncResult>& result) {
            try {
                if (dialog->choose_finish(result) == 1) {
                    reset();
                }
            } catch (const Glib::Error&) {
                // 对话框被关掉，什么也不做。
            }
        });
}

void CaseDock::reset() {
    if (m_case_id.empty()) {
        return;
    }
    try {
        const vector<CaseFile> files = m_workspace.reset(m_case_id);
        m_file_name = files.front().name;
        set_source_text(files.front().contents);
        if (m_file_label) {
            m_file_label->set_text(m_file_name);
        }
        if (m_output_view) {
            m_output_view->get_buffer()->set_text("已恢复成最初的骨架。");
        }
    } catch (const exception& error) {
        if (m_output_view) {
            m_output_view->get_buffer()->set_text(
                "恢复失败：" + string(error.what()));
        }
    }
}
