#include "experiment_runner.h"

#include <glibmm/main.h>

#include <chrono>
#include <iomanip>
#include <sstream>
#include <thread>
#include <utility>

using namespace std;

namespace {

string format_elapsed(double seconds) {
    ostringstream stream;
    stream << fixed << setprecision(2) << seconds << "s";
    return stream.str();
}

} // namespace

struct ExperimentRunner::SharedState {
    atomic_bool running = false;
    thread worker;
};

ExperimentRunner::ExperimentRunner(
    const FunctionRegistry& registry,
    shared_ptr<atomic_bool> ui_alive)
    : m_registry(registry),
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

    state->worker = thread(
        [request,
         on_finished = std::move(on_finished),
         state,
         alive,
         registry]() mutable {
            ExperimentResult result;

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
                [result = std::move(result),
                 on_finished = std::move(on_finished),
                 state,
                 alive]() mutable {
                    if (!alive->load()) {
                        return;
                    }
                    if (state->worker.joinable()) {
                        state->worker.join();
                    }
                    state->running.store(false);

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
