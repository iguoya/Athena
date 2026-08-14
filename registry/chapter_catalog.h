#pragma once

#include <map>
#include <string>
#include <string_view>
#include <vector>

using namespace std;

struct IconSpec {
    string type;
    string name;
    string path;
};

struct SubChapter {
    string name;
    string title;
    string description;
    string group;
    string source;
    IconSpec icon;
};

struct ChapterGroup {
    string name;
    string title;
    string description;
    string source;
    IconSpec icon;
};

struct ChapterMeta {
    string name;
    string title;
    string description;
    string category;
    string content;
    string document;
    string blueprint;
    string resource_path;
    string widget_name;
    string source;
    IconSpec icon;
    vector<ChapterGroup> groups;
    vector<SubChapter> subchapters;
};

struct CategoryInfo {
    string name;
    string title;
    string description;
    IconSpec icon;
};

class ChapterCatalog {
public:
    static ChapterCatalog from_json(string_view source);

    const vector<CategoryInfo>& categories() const;
    const map<string, vector<ChapterMeta>>& chapters() const;
    const ChapterMeta* find_chapter(
        const string& category_name,
        const string& chapter_name) const;
    size_t chapter_count() const;

private:
    vector<CategoryInfo> m_categories;
    map<string, vector<ChapterMeta>> m_chapters;
};

// 知识点源码按“知识点 -> 分组 -> 章节”的顺序继承。
string resolve_source_path(
    const ChapterMeta& chapter,
    const SubChapter& subchapter);
