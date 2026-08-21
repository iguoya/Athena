#include "content/content_loader.h"
#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <fstream>
#include <set>
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

string read_runtime_catalog() {
    ContentLoader loader(ATHENA_SOURCE_ROOT);
    const string source =
        loader.load_resource("/app/data/chapter_catalog.json");
    if (source.empty()) {
        throw runtime_error("Generated runtime Catalog test resource is missing");
    }
    return source;
}

nlohmann::json minimal_catalog() {
    return nlohmann::json::parse(R"JSON({
      "catalog_version": 1,
      "categories": [{
        "name": "cpp",
        "title": "C++",
        "description": "C++ test category",
        "icon": { "type": "theme", "name": "category", "path": "" },
        "handbook_documents": [],
        "chapters": [{
          "name": "Sample",
          "title": "Sample",
          "description": "Sample chapter",
          "overview_document": "",
          "resource_path": "/app/chapters/code.ui",
          "widget_name": "chapter_page",
          "source": "language/sample.cpp",
          "implementation_header": "",
          "icon": { "type": "theme", "name": "chapter", "path": "" },
          "groups": [],
          "subchapters": [{
            "function_id": "cpp.Sample.point",
            "name": "point",
            "title": "Point",
            "description": "Sample point",
            "group": "",
            "source": "language/sample.cpp",
            "importance": 4,
            "icon": { "type": "theme", "name": "point", "path": "" }
          }, {
            "function_id": "cpp.Sample.unrated",
            "name": "unrated",
            "title": "Unrated",
            "description": "No author rating",
            "group": "",
            "source": "language/sample.cpp",
            "importance": 0,
            "icon": { "type": "theme", "name": "point", "path": "" }
          }]
        }]
      }]
    })JSON");
}

TEST(ChapterCatalogTest, LoadsTheGeneratedProjectCatalog) {
    const auto catalog =
        ChapterCatalog::from_runtime_json(read_runtime_catalog());

    const auto author_config =
        nlohmann::json::parse(read_project_file("resources/athena.json"));
    EXPECT_EQ(catalog.categories().size(), author_config.at("categories").size());
    size_t expected_chapters = 0;
    for (const auto& category : author_config.at("categories")) {
        expected_chapters += category.at("chapters").size();
    }
    EXPECT_EQ(catalog.chapter_count(), expected_chapters);

    const auto* reference = catalog.find_chapter("cpp", "Reference");
    ASSERT_NE(reference, nullptr);
    EXPECT_EQ(reference->widget_name, "chapter_page");
    EXPECT_EQ(reference->resource_path, "/app/chapters/empty_chapter.ui");
    EXPECT_EQ(
        reference->implementation_header,
        "language/references/reference.hpp");
    ASSERT_EQ(reference->subchapters.size(), 4);
    EXPECT_EQ(
        reference->subchapters.front().function_id,
        "cpp.Reference.reference_basics");
    EXPECT_EQ(
        reference->overview_document,
        "resources/articles/cpp/reference_overview.md");

    const auto& cpp_handbook = catalog.handbook_documents("cpp");
    EXPECT_NE(
        find(cpp_handbook.begin(), cpp_handbook.end(),
             "resources/articles/cpp/reference_overview.md"),
        cpp_handbook.end());
    EXPECT_TRUE(catalog.handbook_documents("da").empty());
    EXPECT_TRUE(catalog.handbook_documents("no_such_category").empty());
}

TEST(ChapterCatalogTest, GeneratedRegistryExactlyMatchesImplementedChapters) {
    const auto catalog =
        ChapterCatalog::from_runtime_json(read_runtime_catalog());
    const auto registry = create_default_function_registry();

    set<string> expected_ids;
    for (const auto& [category_name, chapters] : catalog.chapters()) {
        for (const auto& chapter : chapters) {
            if (chapter.implementation_header.empty()) {
                continue;
            }
            for (const auto& subchapter : chapter.subchapters) {
                expected_ids.insert(subchapter.function_id);
            }
        }
    }

    const auto ids = registry.ids();
    const set<string> registered_ids(ids.begin(), ids.end());
    EXPECT_EQ(registered_ids, expected_ids);
}

TEST(ChapterCatalogTest, SourcePathsAreResolvedBeforeRuntime) {
    const auto catalog =
        ChapterCatalog::from_runtime_json(read_runtime_catalog());

    const auto* raii = catalog.find_chapter("cpp", "RAII");
    ASSERT_NE(raii, nullptr);
    ASSERT_EQ(raii->subchapters.size(), 6);
    EXPECT_EQ(raii->subchapters[0].source, "language/raii/raii_basic.cpp");
    EXPECT_EQ(raii->subchapters[1].source, "language/raii/smart_pointer.cpp");
    EXPECT_EQ(raii->subchapters[4].source, "language/raii/move_semantics.cpp");

    const auto* reference = catalog.find_chapter("cpp", "Reference");
    ASSERT_NE(reference, nullptr);
    ASSERT_FALSE(reference->subchapters.empty());
    EXPECT_EQ(
        reference->subchapters.front().source,
        "language/references/reference.hpp");
}

TEST(ChapterCatalogTest, DecodesCanonicalRuntimeFields) {
    const auto catalog =
        ChapterCatalog::from_runtime_json(minimal_catalog().dump());
    const auto* chapter = catalog.find_chapter("cpp", "Sample");
    ASSERT_NE(chapter, nullptr);
    ASSERT_EQ(chapter->subchapters.size(), 2u);
    EXPECT_EQ(chapter->subchapters[0].function_id, "cpp.Sample.point");
    EXPECT_EQ(chapter->subchapters[0].importance, 4);
    EXPECT_EQ(chapter->subchapters[1].importance, 0);
    EXPECT_EQ(chapter->icon.name, "chapter");
}

// 作者语义由 Python 保证。受信任解码器既不夹值，也不重新检查 C++ 名称或分组引用。
TEST(ChapterCatalogTest, DoesNotRepairOrRevalidateTrustedAuthorSemantics) {
    auto source = minimal_catalog();
    auto& point = source["categories"][0]["chapters"][0]["subchapters"][0];
    point["name"] = "return";
    point["group"] = "not_declared";
    point["importance"] = 9;

    const auto catalog = ChapterCatalog::from_runtime_json(source.dump());
    const auto* chapter = catalog.find_chapter("cpp", "Sample");
    ASSERT_NE(chapter, nullptr);
    EXPECT_EQ(chapter->subchapters[0].name, "return");
    EXPECT_EQ(chapter->subchapters[0].group, "not_declared");
    EXPECT_EQ(chapter->subchapters[0].importance, 9);
}

TEST(ChapterCatalogTest, RejectsUnsupportedCatalogVersion) {
    auto source = minimal_catalog();
    source["catalog_version"] = 2;
    EXPECT_THROW(
        ChapterCatalog::from_runtime_json(source.dump()),
        runtime_error);
}

TEST(ChapterCatalogTest, ReportsMissingRequiredRuntimeFieldAsCorruption) {
    auto source = minimal_catalog();
    source["categories"][0]["chapters"][0].erase("resource_path");
    try {
        (void)ChapterCatalog::from_runtime_json(source.dump());
        FAIL() << "Expected a corrupted generated Catalog to be rejected";
    } catch (const runtime_error& error) {
        EXPECT_NE(
            string(error.what()).find("Invalid generated runtime chapter Catalog"),
            string::npos);
    }
}

} // namespace
