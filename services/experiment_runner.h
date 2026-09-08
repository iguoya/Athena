#pragma once

#include "registry/function_registry.h"

#include <atomic>
#include <functional>
#include <memory>
#include <string>

using namespace std;

struct ExperimentRequest {
    string function_id;
};

struct ExperimentResult {
    string output;
    string display_output;
    double duration_ms = 0.0;
};

// 标准知识点实验的非 GTK 执行器：同一时刻只运行一个实验，在后台线程
// 调用 FunctionRegistry，再回到主线程交付普通结果对象。页面只负责把结果
// 渲染到控件，不接触线程。
class ExperimentRunner final {
public:
    using Completion = function<void(const ExperimentResult&)>;

    ExperimentRunner(
        const FunctionRegistry& registry,
        shared_ptr<atomic_bool> ui_alive);
    ~ExperimentRunner();

    ExperimentRunner(const ExperimentRunner&) = delete;
    ExperimentRunner& operator=(const ExperimentRunner&) = delete;

    // 已有实验运行时返回 false，不排队；成功启动返回 true。
    bool start(const ExperimentRequest& request, Completion on_finished);
    bool running() const;

private:
    struct SharedState;

    const FunctionRegistry& m_registry;
    shared_ptr<atomic_bool> m_ui_alive;
    shared_ptr<SharedState> m_state;
};
