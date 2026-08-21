#include "chapter_catalog.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <stdexcept>

namespace {

using json = nlohmann::json;

IconSpec parse_icon(const json& value) {
    return {
        .type = value.at("type").get<string>(),
        .name = value.at("name").get<string>(),
        .path = value.at("path").get<string>(),
    };
}

} // namespace

ChapterCatalog ChapterCatalog::from_runtime_json(string_view source) {
    ChapterCatalog catalog;
    try {
        const json config = json::parse(source);
        if (config.at("catalog_version").get<int>() != 1) {
            throw runtime_error("Unsupported runtime chapter Catalog version");
        }

        for (const auto& category_value : config.at("categories")) {
            CategoryInfo category;
            category.name = category_value.at("name").get<string>();
            category.title = category_value.at("title").get<string>();
            category.description = category_value.at("description").get<string>();
            category.icon = parse_icon(category_value.at("icon"));
            for (const auto& document : category_value.at("handbook_documents")) {
                category.handbook_documents.push_back(document.get<string>());
            }
            catalog.m_categories.push_back(category);

            auto& chapters = catalog.m_chapters[category.name];
            for (const auto& chapter_value : category_value.at("chapters")) {
                ChapterMeta chapter;
                chapter.name = chapter_value.at("name").get<string>();
                chapter.title = chapter_value.at("title").get<string>();
                chapter.description = chapter_value.at("description").get<string>();
                chapter.category = category.name;
                chapter.overview_document =
                    chapter_value.at("overview_document").get<string>();
                chapter.resource_path =
                    chapter_value.at("resource_path").get<string>();
                chapter.widget_name = chapter_value.at("widget_name").get<string>();
                chapter.source = chapter_value.at("source").get<string>();
                chapter.implementation_header =
                    chapter_value.at("implementation_header").get<string>();
                chapter.icon = parse_icon(chapter_value.at("icon"));

                for (const auto& group_value : chapter_value.at("groups")) {
                    ChapterGroup group;
                    group.name = group_value.at("name").get<string>();
                    group.title = group_value.at("title").get<string>();
                    group.description =
                        group_value.at("description").get<string>();
                    group.source = group_value.at("source").get<string>();
                    group.icon = parse_icon(group_value.at("icon"));
                    chapter.groups.push_back(std::move(group));
                }

                for (const auto& subchapter_value :
                     chapter_value.at("subchapters")) {
                    SubChapter subchapter;
                    subchapter.function_id =
                        subchapter_value.at("function_id").get<string>();
                    subchapter.name = subchapter_value.at("name").get<string>();
                    subchapter.title = subchapter_value.at("title").get<string>();
                    subchapter.description =
                        subchapter_value.at("description").get<string>();
                    subchapter.group = subchapter_value.at("group").get<string>();
                    subchapter.source = subchapter_value.at("source").get<string>();
                    subchapter.importance =
                        subchapter_value.at("importance").get<int>();
                    subchapter.icon = parse_icon(subchapter_value.at("icon"));
                    chapter.subchapters.push_back(std::move(subchapter));
                }

                chapters.push_back(std::move(chapter));
            }
        }
    } catch (const json::exception& error) {
        throw runtime_error(
            "Invalid generated runtime chapter Catalog: " + string(error.what()));
    }

    return catalog;
}

const vector<CategoryInfo>& ChapterCatalog::categories() const {
    return m_categories;
}

const map<string, vector<ChapterMeta>>& ChapterCatalog::chapters() const {
    return m_chapters;
}

const ChapterMeta* ChapterCatalog::find_chapter(
    const string& category_name,
    const string& chapter_name) const {
    const auto category = m_chapters.find(category_name);
    if (category == m_chapters.end()) {
        return nullptr;
    }

    const auto chapter = find_if(
        category->second.begin(),
        category->second.end(),
        [&chapter_name](const ChapterMeta& value) {
            return value.name == chapter_name;
        });
    return chapter == category->second.end() ? nullptr : &*chapter;
}

size_t ChapterCatalog::chapter_count() const {
    size_t count = 0;
    for (const auto& [category_name, chapters] : m_chapters) {
        count += chapters.size();
    }
    return count;
}

const vector<string>& ChapterCatalog::handbook_documents(
    const string& category_name) const {
    // 分类不存在或没配手册时统一返回同一个空 vector，调用方不必区分。
    static const vector<string> empty;
    const auto found = find_if(
        m_categories.begin(),
        m_categories.end(),
        [&category_name](const CategoryInfo& category) {
            return category.name == category_name;
        });
    return found == m_categories.end() ? empty : found->handbook_documents;
}
