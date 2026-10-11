#include "services/case_runner.h"

#include <gtest/gtest.h>

#include <glib/gstdio.h>
#include <glibmm/fileutils.h>
#include <glibmm/miscutils.h>

#include <chrono>
#include <stdexcept>

using namespace std;

namespace {

void remove_recursive(const string& path) {
    if (Glib::file_test(path, Glib::FileTest::IS_DIR)) {
        Glib::Dir dir(path);
        for (const string& name : dir) {
            remove_recursive(Glib::build_filename(path, name));
        }
    }
    g_remove(path.c_str());
}

struct TempCase {
    string path;

    explicit TempCase(const string& source) {
        GError* error = nullptr;
        char* dir = g_dir_make_tmp("athena-run-test-XXXXXX", &error);
        if (dir == nullptr) {
            const string message = error != nullptr ? error->message : "unknown";
            g_clear_error(&error);
            throw runtime_error("cannot create temp dir: " + message);
        }
        path = dir;
        g_free(dir);
        Glib::file_set_contents(Glib::build_filename(path, "main.cpp"), source);
    }
    ~TempCase() { remove_recursive(path); }

    TempCase(const TempCase&) = delete;
    TempCase& operator=(const TempCase&) = delete;
};

}  // namespace

// 基线假定一台开发机上有编译器（仓库 ADR 0052）。这条不成立时后面几条
// 全无意义，所以单独测一次，失败时看到的是「没有编译器」而不是一堆假象。
TEST(CaseRunnerTest, FindsCompilerOnADeveloperMachine) {
    EXPECT_FALSE(CaseRunner::detect_compiler().empty());
}

TEST(CaseRunnerTest, CompilesAndRuns) {
    const TempCase workspace(
        "#include <iostream>\nint main() { std::cout << \"ok 42\\n\"; }\n");
    const CaseRunResult result = CaseRunner().run(workspace.path);

    EXPECT_TRUE(result.compiled);
    EXPECT_TRUE(result.ran);
    EXPECT_FALSE(result.timed_out);
    EXPECT_EQ(result.exit_status, 0);
    EXPECT_EQ(result.stdout_text, "ok 42\n");
    EXPECT_GT(result.duration_ms, 0.0);
}

TEST(CaseRunnerTest, KeepsCompilerDiagnosticsWhenBuildFails) {
    // 悬垂引用这类错误，编译器说的话本身就是教学内容，不能吞掉。
    const TempCase workspace("int main() { int& r = 1; }\n");
    const CaseRunResult result = CaseRunner().run(workspace.path);

    EXPECT_FALSE(result.compiled);
    EXPECT_FALSE(result.ran);
    EXPECT_FALSE(result.compiler_log.empty());
    EXPECT_NE(result.compiler_log.find("error"), string::npos);
}

TEST(CaseRunnerTest, ReportsNonZeroExit) {
    const TempCase workspace("int main() { return 3; }\n");
    const CaseRunResult result = CaseRunner().run(workspace.path);

    EXPECT_TRUE(result.compiled);
    EXPECT_TRUE(result.ran);
    EXPECT_EQ(result.exit_status, 3);
}

TEST(CaseRunnerTest, KillsRunawayLoop) {
    // 学员写出没有出口的循环是常态，不能让它永久占住那条线程。
    const TempCase workspace("int main() { while (true) {} }\n");
    const CaseRunResult result = CaseRunner(chrono::milliseconds(300)).run(workspace.path);

    EXPECT_TRUE(result.compiled);
    EXPECT_TRUE(result.timed_out);
    EXPECT_FALSE(result.ran);
    EXPECT_NE(result.stderr_text.find("强制结束"), string::npos);
}

TEST(CaseRunnerTest, InstallHintNamesTheThingsThatAreHardToLookUp) {
    const string hint = CaseRunner::install_hint();
    // 只给省时间的那部分：包名、工作负载名（仓库 ADR 0052）。
    EXPECT_NE(hint.find("xcode-select"), string::npos);
    EXPECT_NE(hint.find("使用 C++ 的桌面开发"), string::npos);
    EXPECT_NE(hint.find("build-essential"), string::npos);
}
