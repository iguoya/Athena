#pragma once

#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

using namespace std;

struct IconSpec {
    string type;
    string name;
    string path;
};

// 知识点在手册里的位置：哪份文档、哪一节标题讲到了它。知识点自己声明
// "我在哪一节被讲到"，文档不知道 Athena 存在，不为它改写一个字符；
// heading 按标题文本而不是位置锚点匹配，标题改了配置就该跟着确认。
struct SubChapterTeaches {
    string document;
    string heading;
};

struct SubChapter {
    string function_id;
    string name;
    string title;
    string description;
    string group;
    string source;
    IconSpec icon;
    // 内容作者基于教学与工程实践给出的客观难度评分，0-5；0 = 未评。只读，
    // 不是运行时用户数据；AI 自测得出的熟练度存在 LearningStore 里。
    int importance = 0;
    optional<SubChapterTeaches> teaches;
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
    // “说明文档”按钮跳转目标：手册（见 ChapterCatalog::handbook_documents）
    // 里某一份文档的路径，必须已经在那份列表里（生成器 check 时校验）；
    // 未提供时按钮退回剪贴板 + 唤起本机 AI 助手。文档本身人工撰写、经
    // 审核提交进 git，不发起运行时 AI 调用。
    string overview_document;
    string resource_path;
    string widget_name;
    string source;
    string implementation_header;
    IconSpec icon;
    // 本章依赖的前置章节 name（同分类内）。知识图谱页据此分层布局并画依赖
    // 箭头；生成器已校验引用合法且无环。空表示没有前置（图谱里的起点）。
    vector<string> prerequisites;
    vector<ChapterGroup> groups;
    vector<SubChapter> subchapters;
};

struct CategoryInfo {
    string name;
    string title;
    string description;
    IconSpec icon;
    // 该分类自己的手册：本地静态文档，按此顺序拼接渲染成分类内的一个
    // 手册标签页。手册按分类各自独立，不跨分类合并；跟具体章节解耦，
    // 不要求每份文档都对应一个 chapter，也允许为空（该分类暂无手册）。
    vector<string> handbook_documents;
};

class ChapterCatalog {
public:
    // 只解码生成器产出的受信任 Catalog；作者配置校验由 Python 独占。
    static ChapterCatalog from_runtime_json(string_view source);

    const vector<CategoryInfo>& categories() const;
    const map<string, vector<ChapterMeta>>& chapters() const;
    const ChapterMeta* find_chapter(
        const string& category_name,
        const string& chapter_name) const;
    size_t chapter_count() const;
    // 某个分类的手册文档；分类不存在或没有配手册时返回空 vector。
    const vector<string>& handbook_documents(const string& category_name) const;

private:
    vector<CategoryInfo> m_categories;
    map<string, vector<ChapterMeta>> m_chapters;
};
