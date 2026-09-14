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

TEST(ContentLoaderTest, ReturnsEmptyForMissingProjectFile) {
    const ContentLoader loader("/project");

    EXPECT_TRUE(loader.load_project_file("missing.file").empty());
}

} // namespace
