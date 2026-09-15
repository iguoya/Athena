#include "services/case_workspace.h"

#include <gtest/gtest.h>

#include <glib/gstdio.h>
#include <glibmm/fileutils.h>
#include <glibmm/miscutils.h>

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

// 每个用例一个临时根目录：测试不碰使用者真实的数据目录。
struct TempRoot {
    string path;

    TempRoot() {
        GError* error = nullptr;
        char* dir = g_dir_make_tmp("athena-case-test-XXXXXX", &error);
        if (dir == nullptr) {
            const string message = error != nullptr ? error->message : "unknown";
            g_clear_error(&error);
            throw runtime_error("cannot create temp dir: " + message);
        }
        path = dir;
        g_free(dir);
    }
    ~TempRoot() { remove_recursive(path); }

    TempRoot(const TempRoot&) = delete;
    TempRoot& operator=(const TempRoot&) = delete;
};

SkeletonReader FakeSkeleton() {
    return [](const string&) {
        return vector<CaseFile>{
            CaseFile{.name = "main.cpp", .contents = "int main() { return 0; }\n"},
            CaseFile{.name = "notes.txt", .contents = "原件\n"},
        };
    };
}

}  // namespace

TEST(CaseWorkspaceTest, ExpandsSkeletonOnFirstUse) {
    TempRoot root;
    const CaseWorkspace workspace(root.path, FakeSkeleton());

    const vector<CaseFile> files = workspace.ensure("demo");
    ASSERT_EQ(files.size(), 2u);
    EXPECT_EQ(files[0].name, "main.cpp");
    EXPECT_EQ(files[0].contents, "int main() { return 0; }\n");
    EXPECT_TRUE(Glib::file_test(
        Glib::build_filename(workspace.directory_of("demo"), "main.cpp"),
        Glib::FileTest::EXISTS));
    EXPECT_FALSE(workspace.modified("demo"));
}

TEST(CaseWorkspaceTest, KeepsEditsAcrossEnsure) {
    TempRoot root;
    const CaseWorkspace workspace(root.path, FakeSkeleton());
    workspace.ensure("demo");
    workspace.save("demo", "main.cpp", "int main() { return 42; }\n");

    // 再次打开这个案例不能把学员写的东西冲掉。
    const vector<CaseFile> files = workspace.ensure("demo");
    EXPECT_EQ(files[0].contents, "int main() { return 42; }\n");
    EXPECT_TRUE(workspace.modified("demo"));
}

TEST(CaseWorkspaceTest, ResetRestoresSkeleton) {
    TempRoot root;
    const CaseWorkspace workspace(root.path, FakeSkeleton());
    workspace.ensure("demo");
    workspace.save("demo", "main.cpp", "改坏了\n");
    ASSERT_TRUE(workspace.modified("demo"));

    const vector<CaseFile> files = workspace.reset("demo");
    EXPECT_EQ(files[0].contents, "int main() { return 0; }\n");
    EXPECT_FALSE(workspace.modified("demo"));
}

TEST(CaseWorkspaceTest, RestoresFileDeletedByHand) {
    TempRoot root;
    const CaseWorkspace workspace(root.path, FakeSkeleton());
    workspace.ensure("demo");
    g_remove(Glib::build_filename(workspace.directory_of("demo"), "notes.txt").c_str());

    // 缺一个补一个，不必为了一个文件整个重置。
    const vector<CaseFile> files = workspace.ensure("demo");
    ASSERT_EQ(files.size(), 2u);
    EXPECT_EQ(files[1].contents, "原件\n");
}

TEST(CaseWorkspaceTest, RejectsUnknownFileAndUnsafeIds) {
    TempRoot root;
    const CaseWorkspace workspace(root.path, FakeSkeleton());
    workspace.ensure("demo");

    // 学员改骨架里已有的文件，不新增——驱动和编译命令才不必随副本变化。
    EXPECT_THROW(workspace.save("demo", "extra.cpp", "x"), runtime_error);
    // case id 会拼进文件路径，catalog 被改坏也不能穿出目录。
    EXPECT_THROW(workspace.directory_of("../escape"), runtime_error);
    EXPECT_THROW(workspace.save("demo", "../escape", "x"), runtime_error);
}

// 真实 GResource 里的案例：这条同时验证了生成器把 cases/ 打包进去了。
TEST(CaseWorkspaceTest, ReadsShippedCaseFromResources) {
    const vector<CaseFile> skeleton =
        read_skeleton_from_resources("initialization_forms");
    ASSERT_FALSE(skeleton.empty());
    EXPECT_EQ(skeleton[0].name, "main.cpp");
    EXPECT_NE(skeleton[0].contents.find("int main"), string::npos);
    EXPECT_NE(skeleton[0].contents.find("TODO(学员)"), string::npos);
}

TEST(CaseWorkspaceTest, ReportsMissingCase) {
    EXPECT_THROW(read_skeleton_from_resources("no_such_case"), runtime_error);
}
