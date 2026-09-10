#pragma once

#include "registry/chapter_catalog.h"

#include <map>
#include <string>
#include <vector>

using namespace std;

// 章节级知识图谱：节点是章节，边是"前置依赖"（chapter.prerequisites）。
// 布局按前置关系分层——layer 0 是没有前置的起点，其余取"所有前置层号的
// 最大值 + 1"；同一层内保持 athena.json 的声明顺序。掌握度只用于节点着色，
// 由调用方传入的熟练度记录聚合得到。
//
// 纯计算，不依赖 GTK；渲染在 render/knowledge_graph_view，与 progress_stats
// / chart_view 的分工一致，可脱离 GTK 用 Google Test 验证。
struct KnowledgeNode {
    string chapter_name; // 稳定 name，回调按它定位章节
    string title;
    string description;
    IconSpec icon;
    int layer = 0;
    int slot = 0;        // 层内序号，0..layer_size-1，按声明顺序
    int layer_size = 1;  // 所在层的节点总数，供视图居中排布
    int total = 0;       // 本章知识点总数
    int mastered = 0;    // 5 星知识点数
    // 本章已评知识点 difficulty 的平均值四舍五入到 1-5；全部未评时为 0。
    // 这是章节卡片的汇总展示，不在 athena.json 里重复保存章节级字段。
    int difficulty = 0;
    double completion = 0.0; // 平均熟练度 / 5，落在 [0, 1]
};

struct KnowledgeEdge {
    int from = 0; // nodes 下标：前置章节
    int to = 0;   // nodes 下标：依赖前置的章节
};

struct KnowledgeGraph {
    vector<KnowledgeNode> nodes;
    vector<KnowledgeEdge> edges;
    int layer_count = 0;

    bool empty() const { return nodes.empty(); }
};

// mastery_by_id：function_id -> 熟练度（0-5），只含有过记录的知识点，缺失
// 按 0 处理（与 aggregate_category_progress 口径一致）。分类不存在或没有
// 章节时返回空图。生成器已保证前置引用合法且无环；万一成环，环上节点
// 按 layer 0 处理，不递归爆栈。
KnowledgeGraph build_knowledge_graph(
    const ChapterCatalog& catalog,
    const string& category_name,
    const map<string, int>& mastery_by_id);
