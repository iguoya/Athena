#include "services/case_runner.h"

#include <giomm/init.h>
#include <giomm/subprocess.h>
#include <giomm/subprocesslauncher.h>
#include <glibmm/fileutils.h>
#include <glibmm/miscutils.h>

#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <vector>

using namespace std;

namespace {

// 运行输出的上限。编译诊断不在此列——那是教学内容，完整给。
constexpr size_t kOutputLimit = 200'000;

// 产物名不带后缀：Windows 上编译器自己会补 .exe，运行前两个候选都试一遍，
// 比按平台分叉干净（ADR 0047）。
constexpr const char* kArtifactName = "athena_case";

string clamp_output(string text) {
    if (text.size() > kOutputLimit) {
        text.resize(kOutputLimit);
        text += "\n…（输出过长，已截断）\n";
    }
    return text;
}

// Windows 的 C 运行库在文本模式下把 \n 写成 \r\n，学员程序和编译器的输出
// 都会带上。统一折回 \n，界面与测试看到的是同一份文本；单独的 \r（进度条式
// 回车）不动。
string normalize_newlines(string text) {
    size_t write = 0;
    for (size_t read = 0; read < text.size(); ++read) {
        if (text[read] == '\r' && read + 1 < text.size() && text[read + 1] == '\n') {
            continue;
        }
        text[write++] = text[read];
    }
    text.resize(write);
    return text;
}

string bytes_to_string(const Glib::RefPtr<const Glib::Bytes>& bytes) {
    if (!bytes) {
        return {};
    }
    gsize size = 0;
    const auto* data = static_cast<const char*>(bytes->get_data(size));
    return normalize_newlines(string(data, size));
}

// giomm 的包装表要显式初始化，否则创建 SubprocessLauncher 时拿不到 wrap
// 函数。GTK 应用里 Gtk::Application 会代劳，但本模块要能脱离 GTK 使用
// （测试、将来的命令行入口），所以自己保证一次——Gio::init() 是幂等的。
void ensure_gio_initialized() {
    static once_flag once;
    call_once(once, [] { Gio::init(); });
}

// 编译 work_dir 里的全部 .cpp。一个案例就是一个小程序，全编进去即可。
vector<string> case_sources(const string& work_dir) {
    vector<string> sources;
    Glib::Dir dir(work_dir);
    for (const string& name : dir) {
        const size_t dot = name.rfind('.');
        if (dot == string::npos) {
            continue;
        }
        const string suffix = name.substr(dot);
        if (suffix == ".cpp" || suffix == ".cc" || suffix == ".cxx") {
            sources.push_back(Glib::build_filename(work_dir, name));
        }
    }
    sort(sources.begin(), sources.end());
    return sources;
}

// 跑一个子进程，抓 stdout/stderr。timeout 为零表示不限时。
struct SpawnOutcome {
    bool finished = false;
    bool timed_out = false;
    int exit_status = 0;
    string out;
    string err;
    string spawn_error;
};

SpawnOutcome spawn_and_capture(
    const vector<string>& argv,
    const string& working_directory,
    chrono::milliseconds timeout) {
    ensure_gio_initialized();
    SpawnOutcome outcome;
    Glib::RefPtr<Gio::Subprocess> process;
    try {
        // 用 argv 数组而不是命令行字符串：后者按 shell 规则拆参数，
        // 路径里有空格就散架（ADR 0053 决策第 4 条）。
        const auto launcher = Gio::SubprocessLauncher::create(
            Gio::Subprocess::Flags::STDOUT_PIPE | Gio::Subprocess::Flags::STDERR_PIPE);
        launcher->set_cwd(working_directory);
        process = launcher->spawn(argv);
    } catch (const Glib::Error& error) {
        outcome.spawn_error = error.what();
        return outcome;
    }

    mutex guard;
    condition_variable done_signal;
    bool done = false;
    atomic_bool killed{false};

    // 看门狗：到点还没结束就强杀。communicate() 会因为管道关闭而返回。
    // 用 thread + 显式 join：三平台都能编过，不依赖尚未普遍落地的 jthread。
    thread watchdog([&] {
        if (timeout.count() <= 0) {
            return;
        }
        unique_lock<mutex> lock(guard);
        if (!done_signal.wait_for(lock, timeout, [&] { return done; })) {
            killed = true;
            lock.unlock();
            process->force_exit();
        }
    });

    try {
        const auto [out_bytes, err_bytes] = process->communicate({});
        outcome.out = bytes_to_string(out_bytes);
        outcome.err = bytes_to_string(err_bytes);
        outcome.finished = true;
    } catch (const Glib::Error& error) {
        outcome.spawn_error = error.what();
    }
    {
        lock_guard<mutex> lock(guard);
        done = true;
    }
    done_signal.notify_all();
    if (watchdog.joinable()) {
        watchdog.join();
    }

    outcome.timed_out = killed.load();
    if (outcome.finished && !outcome.timed_out) {
        outcome.exit_status = process->get_if_exited() ? process->get_exit_status() : -1;
    }
    return outcome;
}

}  // namespace

CaseRunner::CaseRunner(chrono::milliseconds timeout) : m_timeout(timeout) {}

string CaseRunner::detect_compiler() {
    // c++ 在 macOS 与多数 Linux 上就是系统默认的那个；MSYS2 的 g++ 也在 PATH 里。
    for (const char* name : {"c++", "clang++", "g++"}) {
        const string path = Glib::find_program_in_path(name);
        if (!path.empty()) {
            return path;
        }
    }
    return {};
}

string CaseRunner::install_hint() {
    return
        "没找到 C++ 编译器。实验要在本机编译运行，装好之后重开本页即可：\n"
        "\n"
        "• macOS：xcode-select --install（装命令行工具，不必装整个 Xcode）\n"
        "• Windows：Visual Studio Installer 里勾「使用 C++ 的桌面开发」工作负载；\n"
        "  用 MSYS2 的话装 mingw-w64-ucrt-x86_64-gcc，并确认在 UCRT64 环境里\n"
        "• Ubuntu / Debian：sudo apt install build-essential";
}

CaseRunResult CaseRunner::run(const string& work_dir) const {
    CaseRunResult result;
    const auto started = chrono::steady_clock::now();
    const auto elapsed_ms = [&started] {
        return chrono::duration<double, milli>(
                   chrono::steady_clock::now() - started).count();
    };

    const string compiler = detect_compiler();
    if (compiler.empty()) {
        result.compiler_log = install_hint();
        result.duration_ms = elapsed_ms();
        return result;
    }

    const vector<string> sources = case_sources(work_dir);
    if (sources.empty()) {
        result.compiler_log = "案例里没有可编译的源文件。";
        result.duration_ms = elapsed_ms();
        return result;
    }

    const string artifact = Glib::build_filename(work_dir, kArtifactName);
    vector<string> compile_argv{compiler, "-std=c++20", "-o", artifact};
    compile_argv.insert(compile_argv.end(), sources.begin(), sources.end());

    // 编译不设超时：慢是正常的，杀掉只会让人困惑。
    const SpawnOutcome compile = spawn_and_capture(
        compile_argv, work_dir, chrono::milliseconds::zero());
    if (!compile.spawn_error.empty()) {
        result.compiler_log = "启动编译器失败：" + compile.spawn_error;
        result.duration_ms = elapsed_ms();
        return result;
    }
    // 诊断走 stderr，个别编译器往 stdout 写，两边都收。完整保留不截断。
    result.compiler_log = compile.err + compile.out;
    if (compile.exit_status != 0) {
        result.duration_ms = elapsed_ms();
        return result;
    }
    result.compiled = true;

    // Windows 上编译器会补 .exe，两个候选都试。
    string executable = artifact;
    if (!Glib::file_test(executable, Glib::FileTest::EXISTS)) {
        executable = artifact + ".exe";
    }
    if (!Glib::file_test(executable, Glib::FileTest::EXISTS)) {
        result.stderr_text = "编译成功，却找不到产物：" + artifact;
        result.duration_ms = elapsed_ms();
        return result;
    }

    const SpawnOutcome run_outcome =
        spawn_and_capture({executable}, work_dir, m_timeout);
    if (!run_outcome.spawn_error.empty() && !run_outcome.timed_out) {
        result.stderr_text = "启动实验失败：" + run_outcome.spawn_error;
        result.duration_ms = elapsed_ms();
        return result;
    }

    result.stdout_text = clamp_output(run_outcome.out);
    result.stderr_text = clamp_output(run_outcome.err);
    result.timed_out = run_outcome.timed_out;
    result.ran = run_outcome.finished && !run_outcome.timed_out;
    result.exit_status = run_outcome.exit_status;
    if (result.timed_out) {
        result.stderr_text +=
            "\n（运行超过 " + to_string(m_timeout.count()) +
            " 毫秒，已强制结束——检查一下是不是有循环没有出口。）\n";
    }
    result.duration_ms = elapsed_ms();
    return result;
}
