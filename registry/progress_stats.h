#pragma once

#include "registry/chapter_catalog.h"

#include <array>
#include <map>
#include <string>
#include <utility>
#include <vector>

using namespace std;

// 熟练度取值范围是 0-5 星，`kMaxMastery` 是满分，`kMasteryLevels` 是直方
// 图的档数（含 0 星那一档）。
constexpr int kMaxMastery = 5;
constexpr size_t kMasteryLevels = kMaxMastery + 1;

// 单个章节的学习进度聚合。
struct ChapterProgress {
    string chapter_title;
    // 知识点标题 -> 熟练度（0-5）；顺序跟 athena.json 里一致。
    vector<pair<string, int>> subchapter_mastery;
    int total = 0;
    int mastered = 0;     // 5 星
    int in_progress = 0;  // 1-4 星
    int mastery_sum = 0;

    // 完成度（0.0-1.0）：平均熟练度占满分的比例，不是"5 星知识点占比"。
    // 后者是二值口径，评到 4 星在图上和完全没学过没有任何区别——实际
    // 数据里几乎没有 5 星时整张柱状图会是空的，看起来像图表没渲染出来。
    double completion_ratio() const;
};

// 一个分类的学习进度聚合。
struct CategoryProgress {
    vector<ChapterProgress> chapters;
    int total = 0;
    int mastered = 0;
    int in_progress = 0;
    int not_started = 0;  // 0 星（含从没评过的）
    int mastery_sum = 0;

    // 平均熟练度（0.0-5.0）；没有知识点时返回 0。
    double average_mastery() const;
    // 熟练度分布：下标即星级，值是该星级的知识点数量。
    array<int, kMasteryLevels> mastery_histogram() const;
};

// 把目录里某个分类的章节与用户熟练度记录交叉聚合。
//
// mastery_by_id 只包含有过记录的知识点（见 LearningStore::load_all_mastery），
// 缺失的按 0 星处理；没有知识点的章节（欢迎页这类）整章跳过，不进
// chapters，也不计入总数。分类不存在时返回空聚合。
CategoryProgress aggregate_category_progress(
    const ChapterCatalog& catalog,
    const string& category_name,
    const map<string, int>& mastery_by_id);

// “接下来建议学什么”的一条结果：只是排序后的展示副本（章节标题 + 知识点
// 标题 + 当前熟练度），不带跳转用的稳定查找键——这是第一版概要功能，
// 先解决“推荐哪些”的排序问题，暂不接可点击跳转；后续如果要点击直接跳到
// 对应知识点，再把 `<category>.<chapter>.<subchapter>` 查找键一起带出来。
struct SuggestedTopic {
    string chapter_title;
    string subchapter_title;
    int mastery = 0;
};

// 从聚合结果里按本地固定规则挑出最多 max_count 个“建议接下来学”的知识点，
// 不调用 AI：优先级是“先学完已经在学的（1-4 星），再开始完全没碰过的
// （0 星）”——已经 5 星的不再推荐。同一优先级内保持 athena.json 里的
// 声明顺序，不做额外排序。这条规则很朴素，只是先把“有没有推荐”这个功能
// 立起来，具体策略以后可以替换（比如按 importance 加权），不需要改调用方。
vector<SuggestedTopic> suggest_next_topics(
    const CategoryProgress& progress, int max_count = 3);
