#include "chapter_catalog.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <set>
#include <stdexcept>

namespace {

using json = nlohmann::json;

IconSpec parse_icon(const json& value, const IconSpec& fallback = {}) {
    if (!value.is_object()) {
        return fallback;
    }

    return {
        .type = value.value("type", ""),
        .name = value.value("name", ""),
        .path = value.value("path", ""),
    };
}

string file_stem(const string& path) {
    const auto slash = path.find_last_of('/');
    const auto filename = slash == string::npos ? path : path.substr(slash + 1);
    const auto dot = filename.find_last_of('.');
    return dot == string::npos ? filename : filename.substr(0, dot);
}

void require_unique(set<string>& names, const string& name, const string& scope) {
    if (!names.insert(name).second) {
        throw runtime_error("Duplicate name '" + name + "' in " + scope);
    }
}

} // namespace

ChapterCatalog ChapterCatalog::from_json(string_view source) {
    const json config = json::parse(source);
    if (config.value("schema", 0) != 1) {
        throw runtime_error("Unsupported athena.json schema");
    }

    const auto& defaults = config.at("defaults");
    const string default_content = defaults.value("content", "code");
    const auto& chapter_ui = defaults.at("chapter_ui");
    const string default_code_blueprint =
        chapter_ui.at("code").at("blueprint").get<string>();
    const string default_article_blueprint =
        chapter_ui.at("article").at("blueprint").get<string>();
    const IconSpec default_chapter_icon =
        parse_icon(defaults.value("chapter_icon", json::object()));
    const IconSpec default_subchapter_icon =
        parse_icon(defaults.value("subchapter_icon", json::object()));

    ChapterCatalog catalog;
    set<string> category_names;

    for (const auto& category_value : config.at("categories")) {
        CategoryInfo category;
        category.name = category_value.at("name").get<string>();
        require_unique(category_names, category.name, "categories");
        category.title = category_value.at("title").get<string>();
        category.description = category_value.at("description").get<string>();
        category.icon = parse_icon(
            category_value.value("icon", json::object()),
            default_chapter_icon);
        catalog.m_categories.push_back(category);

        auto& chapters = catalog.m_chapters[category.name];
        set<string> chapter_names;
        for (const auto& chapter_value : category_value.at("chapters")) {
            ChapterMeta chapter;
            chapter.name = chapter_value.at("name").get<string>();
            require_unique(chapter_names, chapter.name, category.name + " chapters");
            chapter.title = chapter_value.at("title").get<string>();
            chapter.description = chapter_value.at("description").get<string>();
            chapter.category = category.name;
            chapter.content = chapter_value.value("content", default_content);
            if (chapter.content != "code" && chapter.content != "article") {
                throw runtime_error(
                    "Unsupported chapter content type for " + category.name + "." +
                    chapter.name + ": " + chapter.content);
            }

            chapter.document = chapter_value.value("document", "");
            chapter.source = chapter_value.value("source", "");
            chapter.icon = parse_icon(
                chapter_value.value("icon", json::object()),
                default_chapter_icon);
            chapter.blueprint = chapter.content == "article"
                ? default_article_blueprint
                : default_code_blueprint;
            if (chapter_value.contains("ui")) {
                chapter.blueprint = chapter_value.at("ui").value(
                    "blueprint",
                    chapter.blueprint);
            } else if (chapter.content == "article" && chapter.document.empty()) {
                throw runtime_error(
                    "Article chapter requires document: " + category.name + "." +
                    chapter.name);
            }

            const string stem = file_stem(chapter.blueprint);
            chapter.resource_path = "/app/chapters/" + stem + ".ui";
            if (chapter.blueprint == default_code_blueprint) {
                chapter.widget_name = "chapter_page";
            } else if (chapter.blueprint == default_article_blueprint) {
                chapter.widget_name = "article_page";
            } else {
                chapter.widget_name = stem + "_page";
            }

            set<string> group_names;
            for (const auto& group_value :
                 chapter_value.value("groups", json::array())) {
                ChapterGroup group;
                group.name = group_value.at("name").get<string>();
                require_unique(
                    group_names,
                    group.name,
                    category.name + "." + chapter.name + " groups");
                group.title = group_value.at("title").get<string>();
                group.description = group_value.at("description").get<string>();
                group.source = group_value.value("source", "");
                group.icon = parse_icon(
                    group_value.value("icon", json::object()),
                    chapter.icon);
                chapter.groups.push_back(group);
            }

            set<string> subchapter_names;
            for (const auto& subchapter_value : chapter_value.at("subchapters")) {
                SubChapter subchapter;
                subchapter.name = subchapter_value.at("name").get<string>();
                require_unique(
                    subchapter_names,
                    subchapter.name,
                    category.name + "." + chapter.name + " subchapters");
                subchapter.title = subchapter_value.at("title").get<string>();
                subchapter.description =
                    subchapter_value.at("description").get<string>();
                subchapter.group = subchapter_value.value("group", "");
                if (!subchapter.group.empty() &&
                    !group_names.contains(subchapter.group)) {
                    throw runtime_error(
                        "Unknown group '" + subchapter.group + "' in " +
                        category.name + "." + chapter.name + "." +
                        subchapter.name);
                }
                subchapter.source = subchapter_value.value("source", "");
                subchapter.icon = parse_icon(
                    subchapter_value.value("icon", json::object()),
                    default_subchapter_icon);
                chapter.subchapters.push_back(subchapter);
            }

            chapters.push_back(std::move(chapter));
        }
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

string resolve_source_path(
    const ChapterMeta& chapter,
    const SubChapter& subchapter) {
    if (!subchapter.source.empty()) {
        return subchapter.source;
    }

    if (!subchapter.group.empty()) {
        const auto group = find_if(
            chapter.groups.begin(),
            chapter.groups.end(),
            [&subchapter](const ChapterGroup& value) {
                return value.name == subchapter.group;
            });
        if (group != chapter.groups.end() && !group->source.empty()) {
            return group->source;
        }
    }

    return chapter.source;
}
