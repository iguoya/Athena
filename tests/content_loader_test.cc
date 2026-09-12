#include "content/content_loader.h"

#include <gtest/gtest.h>

namespace {

TEST(ContentLoaderTest, LoadsProjectConfigurationFromDisk) {
    const ContentLoader loader(ATHENA_SOURCE_ROOT);

    const string source = loader.load_project_file("resources/athena.json");

    EXPECT_NE(source.find("\"format_version\": 1"), string::npos);
}

TEST(ContentLoaderTest, LoadsTeachingSourceFromBundledResource) {
    const ContentLoader loader("/path/that/does/not/exist");

    const string source = loader.load_project_file(
        "cplusplus/references/reference.hpp");

    EXPECT_NE(source.find("class Reference"), string::npos);
}

// 学习页按 /app/articles/... 取插图（见 type_semantics_lesson_page.cc 的
// lesson_figures）。写成 /app/resources/articles/... 也能编译通过但运行时
// 取不到图，所以这里锁定生产代码真正使用的那条路径。
TEST(ContentLoaderTest, BundlesArticleSvgAssetsAtTheProductionResourcePath) {
    const ContentLoader loader("/path/that/does/not/exist");

    const string image =
        loader.load_resource("/app/articles/cpp/images/init_forms.svg");

    EXPECT_NE(image.find("<svg"), string::npos);
}

TEST(ContentLoaderTest, ReturnsEmptyForMissingProjectFile) {
    const ContentLoader loader("/project");

    EXPECT_TRUE(loader.load_project_file("missing.file").empty());
}

} // namespace
