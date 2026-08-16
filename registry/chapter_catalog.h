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
    // 内容作者基于教学与工程实践给出的客观难度评分，0-5；0 = 未评。只读，
    // 不是运行时用户数据；用户自评的熟练度存在 LearningStore 里。
    int importance = 0;
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
    string implementation_header;
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
