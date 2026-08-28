#include "experiment_runner.h"

#include "content/source_locator.h"

#include <glibmm/main.h>
#include <glibmm/miscutils.h>
#include <glibmm/shell.h>
#include <glibmm/spawn.h>

#include <chrono>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <thread>
#include <utility>

using namespace std;

namespace {

struct GitSourceState {
    string commit;
    bool dirty = false;
};

string format_elapsed(double seconds) {
    ostringstream stream;
    stream << fixed << setprecision(2) << seconds << "s";
    return stream.str();
}

GitSourceState query_git_source_state(
    const string& source_root,
    const string& relative_path) {
    GitSourceState state;
    if (source_root.empty() || relative_path.empty()) {
        return state;
    }

    try {
        string commit_output;
        int exit_status = 0;
        const string commit_command =
            "git -C " + Glib::shell_quote(source_root) + " rev-parse --short HEAD";
        Glib::spawn_command_line_sync(
            commit_command, &commit_output, nullptr, &exit_status);
        if (exit_status != 0) {
            return state;
        }
        while (!commit_output.empty()
               && (commit_output.back() == '\n' || commit_output.back() == '\r')) {
            commit_output.pop_back();
        }
        if (commit_output.empty()) {
            return state;
        }
        state.commit = commit_output;

        string status_output;
        exit_status = 0;
        const string status_command = "git -C " + Glib::shell_quote(source_root)
            + " status --porcelain -- " + Glib::shell_quote(relative_path);
        Glib::spawn_command_line_sync(
            status_command, &status_output, nullptr, &exit_status);
        if (exit_status == 0) {
            state.dirty = !status_output.empty();
        }
    } catch (const exception& error) {
        cerr << "Failed to query git state: " << error.what() << endl;
        return {};
    }
    return state;
}

} // namespace

struct ExperimentRunner::SharedState {
    atomic_bool running = false;
    thread worker;
};

ExperimentRunner::ExperimentRunner(
    const FunctionRegistry& registry,
    const ContentLoader& content_loader,
    LearningStore* learning_store,
    string source_root,
    shared_ptr<atomic_bool> ui_alive)
    : m_registry(registry),
      m_content_loader(content_loader),
      m_learning_store(learning_store),
      m_source_root(std::move(source_root)),
      m_ui_alive(std::move(ui_alive)),
      m_state(make_shared<SharedState>()) {}

ExperimentRunner::~ExperimentRunner() {
    if (m_state->worker.joinable()) {
        m_state->worker.join();
    }
    m_state->running.store(false);
}

bool ExperimentRunner::start(
    const ExperimentRequest& request,
    Completion on_finished) {
    bool expected = false;
    if (!m_state->running.compare_exchange_strong(expected, true)) {
        return false;
    }

    auto state = m_state;
    auto alive = m_ui_alive;
    auto* registry = &m_registry;
    auto* content_loader = &m_content_loader;
    auto* learning_store = m_learning_store;
    const string source_root = m_source_root;

    state->worker = thread(
        [request,
         on_finished = std::move(on_finished),
         state,
         alive,
         registry,
         content_loader,
         learning_store,
         source_root]() mutable {
            ExperimentResult result;
            result.source_snapshot = load_member_source_text(
                *content_loader, request.source_path, request.member_name)
                                         .value_or("");
            const GitSourceState git_state =
                query_git_source_state(source_root, request.source_path);
            result.git_commit = git_state.commit;
            result.git_dirty = git_state.dirty;

            const auto started = chrono::steady_clock::now();
            ostringstream output;
            try {
                registry->run(request.function_id, output);
                result.output = output.str();
            } catch (const exception& error) {
                result.output = "运行失败：" + string(error.what());
            }

            const auto duration = chrono::duration<double>(
                chrono::steady_clock::now() - started);
            result.duration_ms = duration.count() * 1000.0;
            result.display_output = result.output + "\n—— 耗时 "
                + format_elapsed(duration.count()) + " ——";

            Glib::signal_idle().connect_once(
                [request,
                 result = std::move(result),
                 on_finished = std::move(on_finished),
                 state,
                 alive,
                 learning_store]() mutable {
                    if (!alive->load()) {
                        return;
                    }
                    if (state->worker.joinable()) {
                        state->worker.join();
                    }
                    state->running.store(false);

                    if (learning_store) {
                        try {
                            learning_store->record_run(
                                request.function_id,
                                result.output,
                                result.duration_ms,
                                result.source_snapshot,
                                result.git_commit,
                                result.git_dirty);
                        } catch (const exception& error) {
                            cerr << "Failed to record run for "
                                 << request.function_id << ": "
                                 << error.what() << endl;
                        }
                    }
                    if (on_finished) {
                        on_finished(result);
                    }
                });
        });
    return true;
}

bool ExperimentRunner::running() const {
    return m_state->running.load();
}
