#include "registry/chapter_catalog.h"
#include "registry/function_registry.h"

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <fstream>
#include <sstream>
#include <set>
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

string minimal_catalog() {
    return R"JSON({
      "schema": 1,
      "defaults": {
        "chapter_ui": {
          "code": { "blueprint": "resources/ui/chapters/empty_chapter.blp" }
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
    const auto config = read_project_file("resources/athena.json");
    const auto catalog = ChapterCatalog::from_json(config);

    const auto raw = nlohmann::json::parse(config);
    EXPECT_EQ(catalog.categories().size(), raw.at("categories").size());
    size_t expected_chapters = 0;
    for (const auto& category : raw.at("categories")) {
        expected_chapters += category.at("chapters").size();
    }
    EXPECT_EQ(catalog.chapter_count(), expected_chapters);

    const auto* reference = catalog.find_chapter("cpp", "Reference");
    ASSERT_NE(reference, nullptr);
    EXPECT_EQ(reference->widget_name, "chapter_page");
    EXPECT_EQ(
        reference->implementation_header,
        "language/references/reference.hpp");
    ASSERT_EQ(reference->subchapters.size(), 4);
    EXPECT_EQ(reference->subchapters.front().name, "reference_basics");
    EXPECT_EQ(
        reference->overview_document,
        "resources/articles/cpp/reference_overview.md");

    // 手册按分类各自独立：cpp 有自己的一部，引用/RAII 的
    // overview_document 必须落在**本分类**的列表里（由生成器的 check
    // 强制）。
    const auto& cpp_handbook = catalog.handbook_documents("cpp");
    EXPECT_FALSE(cpp_handbook.empty());
    EXPECT_NE(
        find(cpp_handbook.begin(), cpp_handbook.end(),
             "resources/articles/cpp/reference_overview.md"),
        cpp_handbook.end());
    EXPECT_NE(
        find(cpp_handbook.begin(), cpp_handbook.end(),
             "resources/articles/cpp/raii_overview.md"),
        cpp_handbook.end());

    // 还没收录文档的分类返回空列表；不存在的分类同样返回空而不是抛异常，
    // 调用方（手册标签页）不必区分这两种情况。
    EXPECT_TRUE(catalog.handbook_documents("da").empty());
    EXPECT_TRUE(catalog.handbook_documents("dp").empty());
    EXPECT_TRUE(catalog.handbook_documents("no_such_category").empty());
}

// 手册文档挂在分类下，不再有顶层 handbook_documents；旧配置应该报错而
// 不是被静默忽略，否则升级时手册会毫无提示地空掉。
TEST(ChapterCatalogTest, TopLevelHandbookDocumentsAreNotReadAsCategoryHandbook) {
    const auto catalog = ChapterCatalog::from_json(R"({
      "schema": 1,
      "defaults": {
        "chapter_ui": { "code": { "blueprint": "resources/ui/chapters/empty_chapter.blp" } }
      },
      "handbook_documents": ["resources/articles/cpp/reference_overview.md"],
      "categories": [
        {
          "name": "cpp",
          "title": "C++",
          "description": "测试用分类",
          "chapters": []
        }
      ]
    })");

    EXPECT_TRUE(catalog.handbook_documents("cpp").empty());
}

TEST(ChapterCatalogTest, GeneratedRegistryExactlyMatchesImplementedChapters) {
    const auto catalog = ChapterCatalog::from_json(
        read_project_file("resources/athena.json"));
    const auto registry = create_default_function_registry();

    set<string> expected_ids;
    for (const auto& [category_name, chapters] : catalog.chapters()) {
        for (const auto& chapter : chapters) {
            if (chapter.implementation_header.empty()) {
                continue;
            }
            for (const auto& subchapter : chapter.subchapters) {
                expected_ids.insert(make_function_id(
                    category_name,
                    chapter.name,
                    subchapter.name));
            }
        }
    }

    const auto ids = registry.ids();
    const set<string> registered_ids(ids.begin(), ids.end());
    EXPECT_EQ(registered_ids, expected_ids);
}

TEST(ChapterCatalogTest, ResolvesKnowledgePointSourceByPrecedence) {
    const auto catalog = ChapterCatalog::from_json(
        read_project_file("resources/athena.json"));

    const auto* raii = catalog.find_chapter("cpp", "RAII");
    ASSERT_NE(raii, nullptr);
    ASSERT_EQ(raii->subchapters.size(), 6);
    EXPECT_EQ(
        resolve_source_path(*raii, raii->subchapters[0]),
        "language/raii/raii_basic.cpp");
    EXPECT_EQ(
        resolve_source_path(*raii, raii->subchapters[1]),
        "language/raii/smart_pointer.cpp");
    EXPECT_EQ(
        resolve_source_path(*raii, raii->subchapters[4]),
        "language/raii/move_semantics.cpp");

    const auto* reference = catalog.find_chapter("cpp", "Reference");
    ASSERT_NE(reference, nullptr);
    ASSERT_FALSE(reference->subchapters.empty());
    EXPECT_EQ(
        resolve_source_path(*reference, reference->subchapters.front()),
        "language/references/reference.hpp");

    ChapterMeta chapter{.source = "chapter.cpp"};
    chapter.groups.push_back({.name = "group", .source = "group.cpp"});
    SubChapter point{
        .name = "point",
        .group = "group",
        .source = "point.cpp",
    };
    EXPECT_EQ(resolve_source_path(chapter, point), "point.cpp");
    point.source.clear();
    EXPECT_EQ(resolve_source_path(chapter, point), "group.cpp");
    point.group.clear();
    EXPECT_EQ(resolve_source_path(chapter, point), "chapter.cpp");
}

TEST(ChapterCatalogTest, ParsesSubchapterImportanceWithDefault) {
    const string config = R"JSON({
      "schema": 1,
      "defaults": {
        "chapter_ui": {
          "code": { "blueprint": "resources/ui/chapters/empty_chapter.blp" }
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
          "subchapters": [
            { "name": "rated", "title": "Rated", "description": "Has importance", "importance": 4 },
            { "name": "unrated", "title": "Unrated", "description": "No importance field" }
          ]
        }]
      }]
    })JSON";

    const auto catalog = ChapterCatalog::from_json(config);
    const auto* chapter = catalog.find_chapter("cpp", "Sample");
    ASSERT_NE(chapter, nullptr);
    ASSERT_EQ(chapter->subchapters.size(), 2u);
    EXPECT_EQ(chapter->subchapters[0].importance, 4);
    EXPECT_EQ(chapter->subchapters[1].importance, 0);
}

TEST(ChapterCatalogTest, RejectsUnsupportedSchema) {
    string source = minimal_catalog();
    source.replace(source.find("\"schema\": 1"), 11, "\"schema\": 2");
    EXPECT_THROW(ChapterCatalog::from_json(source), runtime_error);
}

} // namespace
