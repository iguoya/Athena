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

TEST(AppPathsTest, FindsExecutableDirectory) {
    const string directory = executable_directory();
    ASSERT_FALSE(directory.empty());
    EXPECT_TRUE(Glib::file_test(directory, Glib::FileTest::IS_DIR));
    // 必须是绝对路径：调用方会拿它拼资源路径，相对路径会随工作目录漂移。
    EXPECT_TRUE(Glib::path_is_absolute(directory));
}

TEST(AppPathsTest, EnvironmentOverridesWin) {
    const ScopedEnv content("ATHENA_CONTENT_ROOT", "/tmp/athena-content");
    const ScopedEnv apps("ATHENA_APPS_ROOT", "/tmp/athena-apps");
    // 覆盖值原样返回，不做存在性检查——部署方明确指定了就照做。
    EXPECT_EQ(content_root(), "/tmp/athena-content");
    EXPECT_EQ(external_apps_root(), "/tmp/athena-apps");
}

TEST(AppPathsTest, ContentRootHoldsTeachingSources) {
    // 没有覆盖时应当落到真实的内容根：判定标志就是 cplusplus/ 在不在。
    const string root = content_root();
    ASSERT_FALSE(root.empty());
    EXPECT_TRUE(Glib::file_test(
        Glib::build_filename(root, "cplusplus"), Glib::FileTest::IS_DIR));
}

TEST(AppPathsTest, ExternalAppsRootHoldsAppManifests) {
    const string apps = external_apps_root();
    ASSERT_FALSE(apps.empty());
    EXPECT_TRUE(Glib::file_test(
        Glib::build_filename(apps, "c", "app.json"),
        Glib::FileTest::EXISTS));
}

} // namespace
