#include "parsing/chapter_catalog.h"

#include <gtest/gtest.h>

#include <fstream>
#include <sstream>
#include <stdexcept>

namespace {

string read_project_file(const string& relative_path) {
    ifstream input(string(ATHENA_SOURCE_ROOT) + "/" + relative_path);
    if (!input) {
        throw runtime_error("Cannot read test fixture: " + relative_path);
    }
    ostringstream content;
    content << input.rdbuf();
    return content.str();
}

string minimal_catalog(
    const string& content = "code",
    const string& document = "") {
    return R"JSON({
      "schema": 1,
      "defaults": {
        "content": "code",
        "chapter_ui": {
          "code": { "blueprint": "resources/ui/chapters/empty_chapter.blp" },
          "article": { "blueprint": "resources/ui/chapters/article_chapter.blp" }
        }
      },
      "categories": [{
        "name": "cpp",
        "title": "C++",
        "description": "C++ test category",
        "chapters": [{
          "name": "Sample",
          "title": "Sample",
          "description": "Sample chapter",
          "content": ")JSON" + content + R"JSON(",
          "document": ")JSON" + document + R"JSON(",
          "subchapters": [{
            "name": "point",
            "title": "Point",
            "description": "Sample point"
          }]
        }]
      }]
    })JSON";
}

TEST(ChapterCatalogTest, LoadsTheProjectCatalog) {
    const auto catalog = ChapterCatalog::from_json(
        read_project_file("resources/athena.json"));

    EXPECT_EQ(catalog.categories().size(), 3);
    EXPECT_EQ(catalog.chapter_count(), 61);

    const auto* reference = catalog.find_chapter("cpp", "Reference");
    ASSERT_NE(reference, nullptr);
    EXPECT_EQ(reference->content, "code");
    EXPECT_EQ(reference->widget_name, "chapter_page");
    ASSERT_EQ(reference->subchapters.size(), 4);
    EXPECT_EQ(reference->subchapters.front().name, "reference_basics");

    const auto* organization =
        catalog.find_chapter("cpp", "ProgramOrganization");
    ASSERT_NE(organization, nullptr);
    EXPECT_EQ(organization->content, "article");
    EXPECT_EQ(
        organization->document,
        "resources/articles/cpp/program_organization.md");
    EXPECT_EQ(organization->widget_name, "article_page");
}

TEST(ChapterCatalogTest, RejectsUnsupportedSchema) {
    string source = minimal_catalog();
    source.replace(source.find("\"schema\": 1"), 11, "\"schema\": 2");
    EXPECT_THROW(ChapterCatalog::from_json(source), runtime_error);
}

TEST(ChapterCatalogTest, RejectsUnsupportedContentType) {
    EXPECT_THROW(ChapterCatalog::from_json(minimal_catalog("video")), runtime_error);
}

TEST(ChapterCatalogTest, RequiresDocumentForDefaultArticlePage) {
    EXPECT_THROW(ChapterCatalog::from_json(minimal_catalog("article")), runtime_error);
    EXPECT_NO_THROW(ChapterCatalog::from_json(
        minimal_catalog("article", "resources/articles/sample.md")));
}

} // namespace
