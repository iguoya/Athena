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
    block.tier = text_or(node, "tier");
    block.caption = text_or(node, "caption");
    block.note = text_or(node, "note");
    block.id = text_or(node, "id");
    block.items = strings_or(node, "items");
    const auto answer = node.find("answer");
    if (answer != node.end() && answer->is_number_integer()) {
        block.answer = answer->get<int>();
    }
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

        const auto parse_topic = [](const json& node) {
            LessonDoc doc;
            doc.topic = node.at("topic").get<string>();
            doc.title = node.at("title").get<string>();
            doc.subtitle = text_or(node, "subtitle");
            for (const auto& block : node.at("blocks")) {
                doc.blocks.push_back(parse_block(block));
            }
            const auto checkpoint = node.find("checkpoint");
            if (checkpoint != node.end()) {
                doc.checkpoint.intro = text_or(*checkpoint, "intro");
                for (const auto& q : checkpoint->at("questions")) {
                    doc.checkpoint.questions.push_back(LessonCheckpointQuestion{
                        .id = q.at("id").get<string>(),
                        .stem = q.at("stem").get<string>(),
                        .options = q.at("options").get<vector<string>>(),
                        .answer = q.at("answer").get<int>(),
                        .explain = q.at("explain").get<string>(),
                    });
                }
            }
            return doc;
        };

        const auto outline = root.find("outline");
        if (outline != root.end()) {
            chapter.outline = parse_topic(*outline);
        }
        for (const auto& topic_node : root.at("topics")) {
            chapter.topics.push_back(parse_topic(topic_node));
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
