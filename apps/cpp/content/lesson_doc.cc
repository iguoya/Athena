#include "content/lesson_doc.h"

#include <giomm/resource.h>
#include <nlohmann/json.hpp>

#include <stdexcept>
#include <utility>

using namespace std;
using json = nlohmann::json;

namespace {

string text_or(const json& node, const char* key) {
    const auto found = node.find(key);
    return found != node.end() && found->is_string() ? found->get<string>() : string();
}

vector<string> strings_or(const json& node, const char* key) {
    vector<string> out;
    const auto found = node.find(key);
    if (found == node.end() || !found->is_array()) {
        return out;
    }
    for (const auto& value : *found) {
        out.push_back(value.get<string>());
    }
    return out;
}

LessonBlock parse_block(const json& node) {
    LessonBlock block;
    block.type = node.at("type").get<string>();
    block.text = text_or(node, "text");
    block.title = text_or(node, "title");
    block.kind = text_or(node, "kind");
    block.caption = text_or(node, "caption");
    block.note = text_or(node, "note");
    block.id = text_or(node, "id");
    block.items = strings_or(node, "items");
    block.head = strings_or(node, "head");

    const auto rows = node.find("rows");
    if (rows != node.end() && rows->is_array()) {
        for (const auto& row : *rows) {
            block.rows.push_back(row.get<vector<string>>());
        }
    }
    const auto children = node.find("blocks");
    if (children != node.end() && children->is_array()) {
        for (const auto& child : *children) {
            block.blocks.push_back(parse_block(child));
        }
    }
    return block;
}

}  // namespace

LessonChapter parse_lesson_chapter(const string& json_text) {
    try {
        const json root = json::parse(json_text);
        LessonChapter chapter;
        chapter.chapter = root.at("chapter").get<string>();
        for (const auto& topic_node : root.at("topics")) {
            LessonDoc doc;
            doc.topic = topic_node.at("topic").get<string>();
            doc.title = topic_node.at("title").get<string>();
            doc.subtitle = text_or(topic_node, "subtitle");
            for (const auto& block : topic_node.at("blocks")) {
                doc.blocks.push_back(parse_block(block));
            }
            chapter.topics.push_back(std::move(doc));
        }
        return chapter;
    } catch (const json::exception& error) {
        throw runtime_error(string("invalid lesson content: ") + error.what());
    }
}

LessonChapter load_lesson_chapter(const string& chapter_id) {
    const string path = "/app/lessons/" + chapter_id + ".json";
    try {
        const Glib::RefPtr<const Glib::Bytes> bytes =
            Gio::Resource::lookup_data_global(path);
        gsize size = 0;
        const auto* data = static_cast<const char*>(bytes->get_data(size));
        return parse_lesson_chapter(string(data, size));
    } catch (const Glib::Error& error) {
        throw runtime_error(
            "cannot read lesson content " + path + ": " + error.what());
    }
}
