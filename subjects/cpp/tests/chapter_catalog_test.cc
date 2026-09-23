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
    ContentLoader loader;
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
        "chapters": [{
          "name": "Sample",
          "title": "Sample",
          "description": "Sample chapter",
          "resource_path": "/app/chapters/code.ui",
          "widget_name": "chapter_page",
          "source": "cplusplus/sample.cpp",
          "implementation_header": "",
          "icon": { "type": "theme", "name": "chapter", "path": "" },
          "groups": [],
          "subchapters": [{
            "function_id": "cpp.Sample.point",
            "name": "point",
            "title": "Point",
            "description": "Sample point",
            "group": "",
            "source": "cplusplus/sample.cpp",
            "difficulty": 4,
            "mastery_goal": "master",
            "knowledge_type": "concept",
            "requires": [],
            "labs": [{
              "case": "sample_case",
              "prompt": "要验证什么",
              "goal": "补哪个符号",
              "hint": "提示"
            }],
            "icon": { "type": "theme", "name": "point", "path": "" }
          }, {
            "function_id": "cpp.Sample.unrated",
            "name": "unrated",
            "title": "Unrated",
            "description": "No author rating",
            "group": "",
            "source": "cplusplus/sample.cpp",
            "difficulty": 0,
            "mastery_goal": "",
            "knowledge_type": "",
            "requires": [],
            "labs": [],
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
        "cplusplus/references/reference.hpp");
    ASSERT_EQ(reference->subchapters.size(), 4);
    EXPECT_EQ(
        reference->subchapters.front().function_id,
        "cpp.Reference.reference_basics");

    const auto* type_semantics = catalog.find_chapter("cpp", "TypeSemantics");
    ASSERT_NE(type_semantics, nullptr);
    EXPECT_EQ(type_semantics->widget_name, "type_semantics_lesson_page");
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

TEST(ChapterCatalogTest, SourcePathsFallBackToHeaderForSingleFileChapters) {
    const auto catalog =
        ChapterCatalog::from_runtime_json(read_runtime_catalog());

    // RAII、TypeSemantics、Reference 都是单文件 .hpp 实现（默认约定，见
    // docs/CHAPTER_CONFIG.md 6.1）：没有任何 subchapter/chapter 级 source
    // 覆盖，继承链 subchapter.source -> chapter.source 最终退到
    // implementation.header 本身，所有知识点解析出同一个源码路径。
    const auto* raii = catalog.find_chapter("cpp", "RAII");
    ASSERT_NE(raii, nullptr);
    // 值语义的两个知识点移去了 ValueSemantics（ADR 0055），RAII 换成纯资源
    // 管理，并按 ADR 0056 补回「裸指针与所有权」作为第一节。
    ASSERT_EQ(raii->subchapters.size(), 5);
    for (const auto& subchapter : raii->subchapters) {
        EXPECT_EQ(subchapter.source, "cplusplus/raii/raii.hpp");
    }

    const auto* type_semantics = catalog.find_chapter("cpp", "TypeSemantics");
    ASSERT_NE(type_semantics, nullptr);
    ASSERT_FALSE(type_semantics->subchapters.empty());
    for (const auto& subchapter : type_semantics->subchapters) {
        EXPECT_EQ(
            subchapter.source,
            "cplusplus/type_semantics/type_semantics.hpp");
    }

    const auto* reference = catalog.find_chapter("cpp", "Reference");
    ASSERT_NE(reference, nullptr);
    ASSERT_FALSE(reference->subchapters.empty());
    EXPECT_EQ(
        reference->subchapters.front().source,
        "cplusplus/references/reference.hpp");
}

TEST(ChapterCatalogTest, DecodesCanonicalRuntimeFields) {
    const auto catalog =
        ChapterCatalog::from_runtime_json(minimal_catalog().dump());
    const auto* chapter = catalog.find_chapter("cpp", "Sample");
    ASSERT_NE(chapter, nullptr);
    ASSERT_EQ(chapter->subchapters.size(), 2u);
    EXPECT_EQ(chapter->subchapters[0].function_id, "cpp.Sample.point");
    EXPECT_EQ(chapter->subchapters[0].difficulty, 4);
    EXPECT_EQ(chapter->subchapters[0].mastery_goal, MasteryGoal::Master);
    EXPECT_EQ(chapter->subchapters[0].knowledge_type, KnowledgeType::Concept);
    EXPECT_TRUE(chapter->subchapters[0].requires_points.empty());
    // 骨架案例（ADR 0053）：挂着的知识点解出题面，没挂的是空的。
    ASSERT_EQ(chapter->subchapters[0].labs.size(), 1u);
    EXPECT_EQ(chapter->subchapters[0].labs[0].case_id, "sample_case");
    EXPECT_EQ(chapter->subchapters[0].labs[0].prompt, "要验证什么");
    EXPECT_EQ(chapter->subchapters[0].labs[0].goal, "补哪个符号");
    EXPECT_EQ(chapter->subchapters[0].labs[0].hint, "提示");
    EXPECT_TRUE(chapter->subchapters[1].labs.empty());
    EXPECT_EQ(chapter->subchapters[1].difficulty, 0);
    EXPECT_EQ(chapter->subchapters[1].mastery_goal, MasteryGoal::Unrated);
    EXPECT_EQ(chapter->icon.name, "chapter");
}

// 作者语义由 Python 保证。受信任解码器既不夹值，也不重新检查 C++ 名称或分组引用。
TEST(ChapterCatalogTest, DoesNotRepairOrRevalidateTrustedAuthorSemantics) {
    auto source = minimal_catalog();
    auto& point = source["categories"][0]["chapters"][0]["subchapters"][0];
    point["name"] = "return";
    point["group"] = "not_declared";
    point["difficulty"] = 9;

    const auto catalog = ChapterCatalog::from_runtime_json(source.dump());
    const auto* chapter = catalog.find_chapter("cpp", "Sample");
    ASSERT_NE(chapter, nullptr);
    EXPECT_EQ(chapter->subchapters[0].name, "return");
    EXPECT_EQ(chapter->subchapters[0].group, "not_declared");
    EXPECT_EQ(chapter->subchapters[0].difficulty, 9);
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
