#pragma once

#include "registry/chapter_catalog.h"

#include <map>
#include <string>
#include <vector>

using namespace std;

// 首页学科知识图谱：节点是"一级学习领域"，边是领域之间的前置依赖。它和
// registry/knowledge_graph（章节级）同构，只是上移一层——把整个平台按
// 计算机 / 电子信息的学习脉络铺开，取代旧的九宫格入口。
//
// 领域分两类：
//  - Available：athena.json 里真有对应分类，进度由该分类全部知识点聚合，
//    点击进入该分类；
//  - Planned：规划中的方向，占位"留空"，灰显、不可点，只给出定位和依赖。
//
// 图谱只收"能验证的实践科目"，每个节点带 VerifyMode（编程 / 开发板 /
// 硬件仪表）。纯理论科目不建节点，用 TheoryTopic 单独列在说明区。
//
// 路线图当前手工维护在 domain_graph.cc。等某个 Planned 领域真正落地成
// 分类，再把它从这张表挪进 athena.json，Available 分支会自动接管展示。
//
// 纯计算，不依赖 GTK；渲染在 render/domain_graph_view，可脱离 GTK 用
// gtest 验证。

enum class DomainKind {
    Available,
    Planned,
};

// 这个领域怎么"验证学到的东西"——图谱的核心筛选维度，突出可实操科目。
enum class VerifyMode {
    Code,  // 在开发机上编程运行、观察输出（平台自带的学练闭环）
    Board, // 需要单片机 / 开发板 / SBC 上板验证
    Bench, // 需要面包板、万用表、示波器、逻辑分析仪、EDA / 打样等硬件条件
};

// 学习优先级：图谱的分层已经是推荐次序，这里再区分"必经主线"和"可选支线"。
enum class DomainPriority {
    Core,        // 核心主线，绝大多数方向都要
    Recommended, // 建议学，按方向取舍
    Optional,    // 可选 / 强方向相关
};

// 领域分组：只影响配色，用一条左侧色条把同族的节点在图上聚成一眼可辨的簇。
enum class DomainTrack {
    Language,    // 编程语言本身
    Engineering, // 结构化与工程方法
    Systems,     // 操作系统 / 系统编程 / 网络
    Hardware,    // 电路与嵌入式
    AI,          // 模型与端侧智能
    Capstone,    // 综合应用
};

// 图谱分两张：计算机（软件 / 系统）方向和电子信息（电路 / 嵌入式）方向。
// 两张各自成图、各自分层，跨方向的依赖单独作为"关联"列出，不混排。
enum class GraphSide {
    Computer,
    Electronics,
};

struct DomainNode {
    string id;      // Available：分类 name；其余：占位标识（稳定、ASCII）
    string title;
    string content;    // 讲什么：主要知识点
    string purpose;    // 作用 / 为什么学：学完能做什么、在体系里的位置
    string difficulty; // 难点：学习时容易卡壳的地方；可空
    IconSpec icon;
    DomainKind kind = DomainKind::Planned;
    VerifyMode verify = VerifyMode::Code;
    DomainPriority priority = DomainPriority::Recommended;
    DomainTrack track = DomainTrack::Language;
    GraphSide side = GraphSide::Computer;
    // 推荐的入门起点：从这些节点里任选一个开始都合理，不必从图的最上层
    // 一路啃。图的纵轴是"知识的来路与依赖"，不是难度或强制次序。
    bool entry = false;
    // 验证方式之外的补充条件，例如"需要逻辑分析仪"、"需要 Linux 环境"；可空。
    string note;

    int layer = 0;      // 在本方向图内的层号
    int slot = 0;       // 本方向同层内的序号，按表中声明顺序
    int layer_size = 1; // 本方向同层的节点数，供视图分列

    // 仅 Available 有意义：
    int total = 0;      // 该分类知识点总数
    int mastered = 0;   // 5 星知识点数
    double completion = 0.0; // 平均熟练度 / 5，落在 [0, 1]
};

struct DomainEdge {
    int from = 0; // nodes 下标：前置领域
    int to = 0;   // nodes 下标：依赖前置的领域
    string reason; // 关联的历史 / 概念来路，以及学前者对后者的必要性
    // strong：真正的前置门槛，B 离开 A 基本学不动。
    // 非 strong：历史 / 概念上的"来路"，画虚线，说明渊源但不是入学门槛
    // （例如汇编 → C：C 从汇编演进而来，但完全可以先学 C 再回头补汇编）。
    bool strong = true;
    // cross：跨方向关联（一端在计算机图、另一端在电子信息图）。
    bool cross = false;
};

// 不建节点的理论科目：只读介绍，内容与作用分开写，放在图谱说明区。
struct TheoryTopic {
    string name;
    string content; // 讲什么
    string role;    // 在实践里起什么作用
};

struct DomainGraph {
    vector<DomainNode> nodes;
    vector<DomainEdge> edges;        // 方向内的依赖（strong / 虚线来路）
    vector<DomainEdge> cross_edges;  // 两张图之间的关联
    vector<TheoryTopic> theory;      // 与节点无关的固定清单
    int computer_layer_count = 0;
    int electronics_layer_count = 0;

    bool empty() const { return nodes.empty(); }
};

// 按内置路线图分层（layer(n) = 0 或所有前置层号最大值 + 1，层内保持声明
// 顺序），为 Available 领域聚合该分类的掌握度，并带出每条边的前置理由和
// 理论科目清单。mastery_by_id 口径与 aggregate_category_progress 一致。
// 路线图里引用了 catalog 没有的分类时，该节点自动降级为 Planned。
DomainGraph build_domain_graph(
    const ChapterCatalog& catalog,
    const map<string, int>& mastery_by_id);
