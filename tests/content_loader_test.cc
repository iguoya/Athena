#include "content/content_loader.h"

#include <gtest/gtest.h>

namespace {

TEST(ContentLoaderTest, LoadsProjectConfigurationFromDisk) {
    const ContentLoader loader(ATHENA_SOURCE_ROOT);

    const string source = loader.load_project_file("resources/athena.json");

    EXPECT_NE(source.find("\"schema\": 1"), string::npos);
}

TEST(ContentLoaderTest, LoadsDocumentWithResourceFallback) {
    const ContentLoader loader(ATHENA_SOURCE_ROOT);

    const string document = loader.load_document(
        "resources/articles/cpp/program_organization.md");

    EXPECT_NE(document.find("从语言知识走向程序组织"), string::npos);
}

TEST(ContentLoaderTest, ResolvesDocumentBaseDirectory) {
    const ContentLoader loader("/project");

    EXPECT_EQ(
        loader.document_base_directory("resources/articles/cpp/lesson.md"),
        "/project/resources/articles/cpp");
    EXPECT_TRUE(loader.load_project_file("missing.file").empty());
}

} // namespace
