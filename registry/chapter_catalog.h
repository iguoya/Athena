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
    // “本章总纲”按钮跳转目标：手册（见 ChapterCatalog::handbook_documents）
    // 里某一份文档的路径，必须已经在那份列表里（生成器 check 时校验）；
    // 未提供时按钮退回剪贴板 + 唤起本机 AI 助手。文档本身人工撰写、经
    // 审核提交进 git，不发起运行时 AI 调用。
    string overview_document;
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
    // 手册：本地静态文档的合集，按此顺序拼接渲染成一个常驻页面；跟具体
    // 章节解耦，不要求每份文档都对应一个 chapter。
    const vector<string>& handbook_documents() const;

private:
    vector<CategoryInfo> m_categories;
    map<string, vector<ChapterMeta>> m_chapters;
    vector<string> m_handbook_documents;
};

// 知识点源码按“知识点 -> 分组 -> 章节”的顺序继承。
string resolve_source_path(
    const ChapterMeta& chapter,
    const SubChapter& subchapter);
