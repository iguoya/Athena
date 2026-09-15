#include "platform/app_paths.h"

#include <glibmm.h>
#include <gtest/gtest.h>

namespace {

// 环境变量在测试之间必须复原，否则会串到同一进程里的其他用例。
class ScopedEnv {
public:
    ScopedEnv(const char* name, const string& value) : m_name(name) {
        // 用 GLib 的接口而不是 POSIX 的 setenv：Windows 上没有后者（ADR 0047）。
        const char* previous = g_getenv(name);
        m_had_previous = previous != nullptr;
        if (m_had_previous) {
            m_previous = previous;
        }
        g_setenv(name, value.c_str(), TRUE);
    }
    ~ScopedEnv() {
        if (m_had_previous) {
            g_setenv(m_name, m_previous.c_str(), TRUE);
        } else {
            g_unsetenv(m_name);
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
    g_unsetenv("ATHENA_APPS_ROOT");

    EXPECT_TRUE(external_apps_root().empty());
}

TEST(AppPathsTest, EmptyWhenPathIsNotDirectory) {
    const ScopedEnv apps(
        "ATHENA_APPS_ROOT",
        Glib::build_filename(Glib::get_tmp_dir(), "athena-apps-does-not-exist"));

    EXPECT_TRUE(external_apps_root().empty());
}

TEST(AppPathsTest, ReadsOwnRootFromEnvironment) {
    const ScopedEnv own("ATHENA_CPP_ROOT", ATHENA_SOURCE_ROOT);

    const string root = own_app_root();

    ASSERT_FALSE(root.empty());
    EXPECT_TRUE(Glib::file_test(
        Glib::build_filename(root, "app.json"), Glib::FileTest::EXISTS));
}

TEST(AppPathsTest, OwnRootEmptyInAReleasePackage) {
    // 发行包里没人传它，进度库就回到本机用户数据目录（ADR 0053）。
    const ScopedEnv own("ATHENA_CPP_ROOT", "");
    g_unsetenv("ATHENA_CPP_ROOT");

    EXPECT_TRUE(own_app_root().empty());
}

} // namespace
