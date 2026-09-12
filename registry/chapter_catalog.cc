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

string mastery_goal_label(MasteryGoal goal) {
    switch (goal) {
    case MasteryGoal::Master:
        return "需要精通";
    case MasteryGoal::Required:
        return "必须掌握";
    case MasteryGoal::Familiar:
        return "一般了解";
    case MasteryGoal::Unrated:
        break;
    }
    return "";
}

string knowledge_type_label(KnowledgeType type) {
    switch (type) {
    case KnowledgeType::Concept:
        return "概念";
    case KnowledgeType::Skill:
        return "技能";
    case KnowledgeType::Strategy:
        return "策略";
    case KnowledgeType::Unrated:
        break;
    }
    return "";
}

KnowledgeType parse_knowledge_type(const string& value) {
    if (value == "concept") {
        return KnowledgeType::Concept;
    }
    if (value == "skill") {
        return KnowledgeType::Skill;
    }
    if (value == "strategy") {
        return KnowledgeType::Strategy;
    }
    return KnowledgeType::Unrated;
}

MasteryGoal parse_mastery_goal(const string& value) {
    if (value == "master") {
        return MasteryGoal::Master;
    }
    if (value == "required") {
        return MasteryGoal::Required;
    }
    if (value == "familiar") {
        return MasteryGoal::Familiar;
    }
    return MasteryGoal::Unrated;
}

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
            catalog.m_categories.push_back(category);

            auto& chapters = catalog.m_chapters[category.name];
            for (const auto& chapter_value : category_value.at("chapters")) {
                ChapterMeta chapter;
                chapter.name = chapter_value.at("name").get<string>();
                chapter.title = chapter_value.at("title").get<string>();
                chapter.description = chapter_value.at("description").get<string>();
                chapter.category = category.name;
                chapter.resource_path =
                    chapter_value.at("resource_path").get<string>();
                chapter.widget_name = chapter_value.at("widget_name").get<string>();
                chapter.source = chapter_value.at("source").get<string>();
                chapter.implementation_header =
                    chapter_value.at("implementation_header").get<string>();
                chapter.icon = parse_icon(chapter_value.at("icon"));

                if (chapter_value.contains("prerequisites")) {
                    for (const auto& prerequisite :
                         chapter_value.at("prerequisites")) {
                        chapter.prerequisites.push_back(
                            prerequisite.get<string>());
                    }
                }

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
                    subchapter.difficulty =
                        subchapter_value.at("difficulty").get<int>();
                    subchapter.mastery_goal = parse_mastery_goal(
                        subchapter_value.at("mastery_goal").get<string>());
                    subchapter.knowledge_type = parse_knowledge_type(
                        subchapter_value.at("knowledge_type").get<string>());
                    for (const auto& required :
                         subchapter_value.at("requires")) {
                        subchapter.requires_points.push_back(
                            SubChapterRequirement{
                                .function_id =
                                    required.at("function_id").get<string>(),
                                .title = required.at("title").get<string>(),
                                .chapter_title =
                                    required.at("chapter_title").get<string>(),
                                .same_chapter =
                                    required.at("same_chapter").get<bool>(),
                            });
                    }
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

const SubChapter* ChapterCatalog::find_subchapter(const string& function_id) const {
    for (const auto& [category_name, chapters] : m_chapters) {
        for (const auto& chapter : chapters) {
            for (const auto& subchapter : chapter.subchapters) {
                if (subchapter.function_id == function_id) {
                    return &subchapter;
                }
            }
        }
    }
    return nullptr;
}
