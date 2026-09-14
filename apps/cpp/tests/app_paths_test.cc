#include "platform/app_paths.h"

#include <glibmm.h>
#include <gtest/gtest.h>

#include <cstdlib>

namespace {

// 环境变量在测试之间必须复原，否则会串到同一进程里的其他用例。
class ScopedEnv {
public:
    ScopedEnv(const char* name, const string& value) : m_name(name) {
        const char* previous = getenv(name);
        m_had_previous = previous != nullptr;
        if (m_had_previous) {
            m_previous = previous;
        }
        setenv(name, value.c_str(), 1);
    }
    ~ScopedEnv() {
        if (m_had_previous) {
            setenv(m_name, m_previous.c_str(), 1);
        } else {
            unsetenv(m_name);
        }
    }

private:
    const char* m_name;
    bool m_had_previous = false;
    string m_previous;
};

TEST(AppPathsTest, ReadsAppsRootFromEnvironment) {
    const ScopedEnv apps("ATHENA_APPS_ROOT", ATHENA_SOURCE_ROOT "/../../apps");

    const string root = external_apps_root();

    ASSERT_FALSE(root.empty());
    EXPECT_TRUE(Glib::file_test(
        Glib::build_filename(root, "c", "app.json"), Glib::FileTest::EXISTS));
}

TEST(AppPathsTest, EmptyWhenEnvironmentMissing) {
    // 没人告诉它 apps/ 在哪就返回空，由调用方提示改用启动器（ADR 0047）——
    // 不自己去猜别的应用住在哪。
    const ScopedEnv apps("ATHENA_APPS_ROOT", "");
    unsetenv("ATHENA_APPS_ROOT");

    EXPECT_TRUE(external_apps_root().empty());
}

TEST(AppPathsTest, EmptyWhenPathIsNotDirectory) {
    const ScopedEnv apps("ATHENA_APPS_ROOT", "/tmp/athena-apps-does-not-exist");

    EXPECT_TRUE(external_apps_root().empty());
}

} // namespace
