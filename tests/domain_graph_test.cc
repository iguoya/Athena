#include "registry/domain_graph.h"

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

#include <algorithm>

namespace {

using json = nlohmann::json;

const json kIcon = {{"type", "theme"}, {"name", "test"}, {"path", ""}};

json MakePoint(const string& function_id, const string& name) {
    return json{
        {"function_id", function_id},
        {"name", name},
        {"title", name},
        {"description", "d"},
        {"group", ""},
        {"source", ""},
        {"importance", 0},
        {"icon", kIcon},
    };
}

json MakeChapter(const string& name, json subchapters) {
    return json{
        {"name", name},
        {"title", name + " 章"},
        {"description", "章"},
        {"overview_document", ""},
        {"resource_path", "/app/chapters/code.ui"},
        {"widget_name", "chapter_page"},
        {"source", ""},
        {"implementation_header", ""},
        {"icon", kIcon},
        {"prerequisites", json::array()},
        {"groups", json::array()},
        {"subchapters", std::move(subchapters)},
    };
}

// 只有 cpp 一个真实分类：da / dp / practice 在路线图里标 Available，但
// catalog 查无此分类，应降级为 Planned。
ChapterCatalog MakeCatalog() {
    const json source = {
        {"catalog_version", 1},
        {"categories", json::array({
            {
                {"name", "cpp"},
                {"title", "C++ 真实标题"},
                {"description", "真实简介"},
                {"icon", kIcon},
                {"handbook_documents", json::array()},
                {"chapters", json::array({
                    MakeChapter("A", json::array({
                        MakePoint("cpp.A.a1", "a1"),
                        MakePoint("cpp.A.a2", "a2"),
                    })),
                })},
            },
        })},
    };
    return ChapterCatalog::from_runtime_json(source.dump());
}

const DomainNode& NodeById(const DomainGraph& graph, const string& id) {
    const auto found = std::find_if(
        graph.nodes.begin(), graph.nodes.end(),
        [&id](const DomainNode& node) { return node.id == id; });
    EXPECT_NE(found, graph.nodes.end()) << id;
    return *found;
}

int IndexOf(const DomainGraph& graph, const string& id) {
    return static_cast<int>(&NodeById(graph, id) - graph.nodes.data());
}

bool HasEdge(
    const vector<DomainEdge>& edges,
    const DomainGraph& graph,
    const string& from,
    const string& to) {
    const int f = IndexOf(graph, from);
    const int t = IndexOf(graph, to);
    return std::any_of(edges.begin(), edges.end(), [&](const DomainEdge& e) {
        return e.from == f && e.to == t;
    });
}

TEST(DomainGraphTest, AvailableDomainPullsCatalogMetadataAndProgress) {
    const auto graph = build_domain_graph(MakeCatalog(), {{"cpp.A.a1", 5}});

    const auto& cpp = NodeById(graph, "cpp");
    EXPECT_EQ(cpp.kind, DomainKind::Available);
    EXPECT_EQ(cpp.title, "C++ 真实标题");
    EXPECT_EQ(cpp.content, "真实简介"); // Available 用分类描述覆盖 content
    EXPECT_FALSE(cpp.purpose.empty()); // purpose 仍来自路线图表
    EXPECT_EQ(cpp.total, 2);
    EXPECT_EQ(cpp.mastered, 1);
    EXPECT_NEAR(cpp.completion, 0.5, 1e-9); // 熟练度和 5 / (5 * 2)
}

TEST(DomainGraphTest, MissingCategoryDowngradesToPlanned) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    EXPECT_EQ(NodeById(graph, "practice").kind, DomainKind::Planned);
    EXPECT_EQ(NodeById(graph, "da").kind, DomainKind::Planned);
    EXPECT_EQ(NodeById(graph, "practice").total, 0);
}

TEST(DomainGraphTest, NodesSplitIntoTwoSideGraphs) {
    const auto graph = build_domain_graph(MakeCatalog(), {});

    EXPECT_EQ(NodeById(graph, "cpp").side, GraphSide::Computer);
    EXPECT_EQ(NodeById(graph, "linux_sysprog").side, GraphSide::Computer);
    EXPECT_EQ(NodeById(graph, "electronics_basics").side,
              GraphSide::Electronics);
    EXPECT_EQ(NodeById(graph, "stm32").side, GraphSide::Electronics);
    EXPECT_EQ(NodeById(graph, "edge_ai").side, GraphSide::Electronics);
    EXPECT_GT(graph.computer_layer_count, 0);
    EXPECT_GT(graph.electronics_layer_count, 0);
}

TEST(DomainGraphTest, RootsHaveNoPrerequisiteAndSitAtLayerZero) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    // 这些模块本来就独立，不该被硬连到别的节点。
    for (const char* id :
         {"assembly", "computer_systems", "engineering_practice",
          "python", "electronics_basics"}) {
        EXPECT_EQ(NodeById(graph, id).layer, 0) << id;
        EXPECT_FALSE(HasEdge(graph.edges, graph, "cpp", id)) << id;
    }
}

TEST(DomainGraphTest, CppIsPrerequisiteOfDataStructures) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    // 本平台的数据结构课是用 C++ 手写实现的——C++ 是它的前置，
    // 层号在 C++ 右侧（更深）。
    EXPECT_TRUE(HasEdge(graph.edges, graph, "cpp", "da"));
    EXPECT_GT(NodeById(graph, "da").layer, NodeById(graph, "cpp").layer);
    const auto e = std::find_if(
        graph.edges.begin(), graph.edges.end(), [&](const DomainEdge& x) {
            return x.from == IndexOf(graph, "cpp") &&
                   x.to == IndexOf(graph, "da");
        });
    ASSERT_NE(e, graph.edges.end());
    EXPECT_TRUE(e->strong);
    EXPECT_FALSE(e->reason.empty());
}

TEST(DomainGraphTest, ComputerNetworksIsAHandsOnNodeNotJustTheory) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    const auto& net = NodeById(graph, "computer_networks");
    EXPECT_EQ(net.side, GraphSide::Computer);
    EXPECT_EQ(net.verify, VerifyMode::Code); // 可编程验证：抓包 / 协议栈
    EXPECT_EQ(net.priority, DomainPriority::Core);
    EXPECT_TRUE(HasEdge(graph.edges, graph, "linux_sysprog",
                        "computer_networks"));
    EXPECT_TRUE(HasEdge(graph.edges, graph, "computer_networks",
                        "network_programming"));
    // 理论科目里不再重复列"计算机网络原理"。
    for (const auto& t : graph.theory) {
        EXPECT_NE(t.name, "计算机网络原理");
    }
}

TEST(DomainGraphTest, LanguageLineageFollowsHistory) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    // 汇编 → C → C++：历史 / 概念来路，画虚线（strong == false）。
    EXPECT_EQ(NodeById(graph, "assembly").layer, 0);
    EXPECT_EQ(NodeById(graph, "c_lang").layer, 1);
    EXPECT_EQ(NodeById(graph, "cpp").layer, 2);

    const auto weak = std::find_if(
        graph.edges.begin(), graph.edges.end(), [&](const DomainEdge& e) {
            return e.from == IndexOf(graph, "assembly") &&
                   e.to == IndexOf(graph, "c_lang");
        });
    ASSERT_NE(weak, graph.edges.end());
    EXPECT_FALSE(weak->strong);
    EXPECT_FALSE(weak->reason.empty());
}

TEST(DomainGraphTest, CppIsNotForcedAsTheRootOfEverything) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    // Python、计算机系统、工程实践与 C++ 没有真实依赖，不连线。
    EXPECT_FALSE(HasEdge(graph.edges, graph, "cpp", "python"));
    EXPECT_FALSE(HasEdge(graph.edges, graph, "cpp", "computer_systems"));
    EXPECT_FALSE(HasEdge(graph.edges, graph, "cpp", "engineering_practice"));
    EXPECT_FALSE(HasEdge(graph.cross_edges, graph, "cpp", "python"));
}

TEST(DomainGraphTest, EmbeddedChainDeepensLayerByLayer) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    EXPECT_EQ(NodeById(graph, "electronics_basics").layer, 0);
    EXPECT_EQ(NodeById(graph, "mcu_8051").layer, 1);
    EXPECT_EQ(NodeById(graph, "stm32").layer, 2);
    EXPECT_EQ(NodeById(graph, "freertos").layer, 3);
}

TEST(DomainGraphTest, FpgaAndSensorsAreEarlyElectronicsBranches) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    // FPGA / 传感器与单片机并列，都直接从电路基础长出。
    EXPECT_EQ(NodeById(graph, "fpga").side, GraphSide::Electronics);
    EXPECT_EQ(NodeById(graph, "sensors").side, GraphSide::Electronics);
    EXPECT_EQ(NodeById(graph, "fpga").layer, 1);
    EXPECT_EQ(NodeById(graph, "sensors").layer, 1);
    EXPECT_TRUE(HasEdge(graph.edges, graph, "electronics_basics", "fpga"));
    EXPECT_TRUE(HasEdge(graph.edges, graph, "sensors", "dsp"));
    // DSP / 电机控制 / 嵌入式 Linux 都在电子信息图里。
    EXPECT_EQ(NodeById(graph, "dsp").side, GraphSide::Electronics);
    EXPECT_EQ(NodeById(graph, "motor_control").side, GraphSide::Electronics);
    EXPECT_EQ(NodeById(graph, "embedded_linux").side, GraphSide::Electronics);
    // Linux 驱动现在有同方向前置（嵌入式 Linux），不再孤立在第 0 层。
    EXPECT_GT(NodeById(graph, "linux_driver").layer, 0);
}

TEST(DomainGraphTest, CrossSideDependenciesGoToCrossEdges) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    // c_lang（计算机）→ mcu_8051（电子信息）是跨方向关联。
    EXPECT_TRUE(HasEdge(graph.cross_edges, graph, "c_lang", "mcu_8051"));
    EXPECT_TRUE(HasEdge(graph.cross_edges, graph, "model_dev", "edge_ai"));
    // 不能出现在方向内 edges 里。
    EXPECT_FALSE(HasEdge(graph.edges, graph, "c_lang", "mcu_8051"));
    for (const auto& e : graph.cross_edges) {
        EXPECT_NE(graph.nodes[static_cast<size_t>(e.from)].side,
                  graph.nodes[static_cast<size_t>(e.to)].side);
    }
}

TEST(DomainGraphTest, EveryEdgeHasAReason) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    ASSERT_FALSE(graph.edges.empty());
    ASSERT_FALSE(graph.cross_edges.empty());
    for (const auto& e : graph.edges) {
        EXPECT_FALSE(e.reason.empty());
    }
    for (const auto& e : graph.cross_edges) {
        EXPECT_FALSE(e.reason.empty());
    }
}

TEST(DomainGraphTest, EntryPointsAreMarked) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    for (const char* id :
         {"cpp", "python", "electronics_basics", "engineering_practice"}) {
        EXPECT_TRUE(NodeById(graph, id).entry) << id;
    }
    // da 现在依赖 C++，不再作为独立入门起点。
    EXPECT_FALSE(NodeById(graph, "da").entry);
    EXPECT_FALSE(NodeById(graph, "linux_driver").entry);
}

TEST(DomainGraphTest, VerifyModeMarksHowEachDomainIsChecked) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    EXPECT_EQ(NodeById(graph, "cpp").verify, VerifyMode::Code);
    EXPECT_EQ(NodeById(graph, "mcu_8051").verify, VerifyMode::Board);
    EXPECT_EQ(NodeById(graph, "electronics_basics").verify, VerifyMode::Bench);
    EXPECT_EQ(NodeById(graph, "pcb_design").verify, VerifyMode::Bench);
}

TEST(DomainGraphTest, PriorityAndTrackAreAssigned) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    EXPECT_EQ(NodeById(graph, "cpp").priority, DomainPriority::Core);
    EXPECT_EQ(NodeById(graph, "model_dev").priority, DomainPriority::Optional);
    EXPECT_EQ(NodeById(graph, "cpp").track, DomainTrack::Language);
    EXPECT_EQ(NodeById(graph, "stm32").track, DomainTrack::Hardware);
    EXPECT_EQ(NodeById(graph, "practice").track, DomainTrack::Capstone);
}

TEST(DomainGraphTest, TheoryTopicsSeparateContentAndRole) {
    const auto graph = build_domain_graph(MakeCatalog(), {});
    EXPECT_GE(graph.theory.size(), 5u);
    for (const auto& topic : graph.theory) {
        EXPECT_FALSE(topic.name.empty());
        EXPECT_FALSE(topic.content.empty());
        EXPECT_FALSE(topic.role.empty());
    }
}

} // namespace
