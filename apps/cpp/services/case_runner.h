#pragma once

#include <chrono>
#include <string>

using namespace std;

// 骨架案例的编译与运行结果（ADR 0053）。
struct CaseRunResult {
    // 编译是否成功。失败时 compiler_log 就是全部产出。
    bool compiled = false;
    // 运行是否正常结束（超时或被杀不算）。
    bool ran = false;
    bool timed_out = false;
    // 编译器诊断，**不截断**：看懂 error: cannot bind non-const lvalue
    // reference 本身就是学 C++ 的一部分，截断等于把教学内容砍掉。
    string compiler_log;
    string stdout_text;
    string stderr_text;
    int exit_status = 0;
    double duration_ms = 0.0;
};

// 编译并运行工作副本。不依赖 GTK，调用方负责放到后台线程去跑。
class CaseRunner final {
public:
    // timeout 管的是运行阶段：学员写出死循环是常态，不能让它永久占住线程。
    // 编译阶段不设超时——编译慢是正常的，杀掉只会让人困惑。
    explicit CaseRunner(chrono::milliseconds timeout = chrono::seconds(10));

    // 编译 work_dir 下的全部 .cpp 并运行产物。
    CaseRunResult run(const string& work_dir) const;

    // 本机 C++ 编译器的绝对路径，找不到返回空串。
    static string detect_compiler();

    // 找不到编译器时给使用者看的话。只写查起来费事的那部分——
    // 官网地址、「LLVM 带 clang++」之类的常识不写（仓库 ADR 0052）。
    static string install_hint();

private:
    chrono::milliseconds m_timeout;
};
