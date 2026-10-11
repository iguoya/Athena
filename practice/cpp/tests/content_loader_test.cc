#include "content/content_loader.h"

#include <gtest/gtest.h>

namespace {

TEST(ContentLoaderTest, LoadsGeneratedCatalogFromResource) {
    const ContentLoader loader;

    // 章节目录是生成的，随构建打进 GResource——运行期不按文件路径找它
    // （ADR 0047）。
    const string catalog = loader.load_resource("/app/data/chapter_catalog.json");

    EXPECT_NE(catalog.find("categories"), string::npos);
}

TEST(ContentLoaderTest, LoadsTeachingSourceFromBundledResource) {
    const ContentLoader loader;

    const string source = loader.load_project_file(
        "cplusplus/references/reference.hpp");

    EXPECT_NE(source.find("class Reference"), string::npos);
}

TEST(ContentLoaderTest, ReturnsEmptyForMissingProjectFile) {
    const ContentLoader loader;

    EXPECT_TRUE(loader.load_project_file("missing.file").empty());
}

} // namespace
