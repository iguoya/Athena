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

// 一条前置依赖。生成器已把标题一并展开，界面直接显示，不必反查 Catalog。
struct SubChapterRequirement {
    string function_id;
    string title;
    string chapter_title;
    bool same_chapter = true;
};

// 知识类型：决定这个知识点该用哪种教学动作（ADR 0031）。
enum class KnowledgeType {
    Unrated,  // 未评定
    Concept,  // 概念：正反例辨析、边界案例、分类判断
    Skill,    // 程序性技能：示范 → 模仿 → 变式练习 → 反馈
    Strategy, // 条件性策略：情境判断、说明依据与代价
};

string knowledge_type_label(KnowledgeType type);
KnowledgeType parse_knowledge_type(const string& value);

// 掌握目标：这个知识点要学到什么程度，与难度分开评定。
// 只按重要性评定：用错的代价、是不是后续内容的地基、能不能靠编译器兜底。
// 不看出现频率——低频高危的东西（漏写 virtual 析构）恰恰最该精通。
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

// 可编辑骨架案例（ADR 0053）。案例源码随 GResource 分发，运行期展开成用户
// 数据目录下的工作副本供学员编辑；这里只带定位信息与题面。
struct LabSpec {
    // 案例目录名。仓库里在 resources/cases/<case_id>/，发布后在
    // GResource 的 /app/cases/<case_id>/ 下。JSON 字段叫 case，
    // 那是 C++ 关键字，所以这里换个名字。
    string case_id;
    // 题干：这道实验要验证或解决什么、观察什么现象。读者第一眼读这个。
    string prompt;
    // 动手清单：补哪个符号、对照哪段输出。
    string goal;
    // 可选提示；没有就是空串。
    string hint;
};

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
    // knowledge_type：概念 / 技能 / 策略，学习页据此选择教学动作。
    KnowledgeType knowledge_type = KnowledgeType::Unrated;
    // requires：学这个知识点之前应当先掌握的知识点，完整函数 ID。生成器已校验
    // 存在性、无环，以及跨章依赖与章节 prerequisites 同向（ADR 0030）。
    vector<SubChapterRequirement> requires_points;
    // labs：这个知识点挂的可编辑骨架案例（ADR 0053），可以为空。与
    // FunctionRegistry 的只读实验并存：只读那条给「看懂它长什么样」，
    // 案例这条给「自己写一遍」。
    vector<LabSpec> labs;
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
    // 按完整函数 ID 找知识点，用于解析 requires 里的跨章前置；找不到返回 nullptr。
    const SubChapter* find_subchapter(const string& function_id) const;

private:
    vector<CategoryInfo> m_categories;
    map<string, vector<ChapterMeta>> m_chapters;
};
