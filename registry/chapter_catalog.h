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

// 掌握目标：这个知识点要学到什么程度，与难度分开评定。
enum class MasteryGoal {
    Unrated,  // 未评定（练习类章节）
    Master,   // 需要精通：反复使用，要能解释边界并写对
    Required, // 必须掌握：能正确使用并说明选择依据
    Familiar, // 一般了解：知道存在与适用场景，需要时能查
};

// 界面显示用的中文名，未评定时返回空串。
string mastery_goal_label(MasteryGoal goal);
// 配置里的字符串值（master / required / familiar）转枚举，无法识别时为 Unrated。
MasteryGoal parse_mastery_goal(const string& value);

struct SubChapter {
    string function_id;
    string name;
    string title;
    string description;
    string group;
    string source;
    IconSpec icon;
    // 内容作者给出的两个独立维度（ADR 0029），都是只读的内容元数据，不是运行时
    // 用户数据；AI 自测得出的熟练度存在 LearningStore 里。
    //
    // difficulty：这个知识点本身有多难，0-5，0 = 未评。1-3 属于初中级，
    // 4-5 属于高级，初学者可以先跳过再回来。
    int difficulty = 0;
    // mastery_goal：学完本章后要达到什么程度。难度高不代表可以不掌握
    // （移动语义就是），难度低也不代表只需了解。
    MasteryGoal mastery_goal = MasteryGoal::Unrated;
    optional<SubChapterTeaches> teaches;
};

struct ChapterGroup {
    string name;
    string title;
    string description;
    string source;
    IconSpec icon;
};

// 一条嵌在某节叙述之后的微型学习循环（ADR 0025）。它只保存已校验的
// 内容与稳定实验 ID；选择状态属于 UI，不写回 Catalog 或数据库。
struct LearningUnit {
    string id;
    string heading;
    string claim;
    string question;
    vector<string> choices;
    size_t correct_choice = 0;
    string feedback;
    string follow_up;
    string experiment_function_id;
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
    vector<LearningUnit> learning_units;
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
