#include "registry/knowledge_graph.h"

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

#include <algorithm>

namespace {

using json = nlohmann::json;

const json kIcon = {{"type", "theme"}, {"name", "test"}, {"path", ""}};

json MakePoint(
    const string& chapter, const string& name, int difficulty = 0) {
    return json{
        {"function_id", "cpp." + chapter + "." + name},
        {"name", name},
        {"title", name},
        {"description", "d"},
        {"group", ""},
        {"source", ""},
        {"difficulty", difficulty},
        {"mastery_goal", ""},
        {"knowledge_type", ""},
        {"requires", json::array()},
        {"icon", kIcon},
    };
}

json MakeChapter(
    const string& name,
    json prerequisites,
    json subchapters,
    const string& implementation_header = "") {
    return json{
        {"name", name},
        {"title", name + " 章"},
        {"description", "测试章节"},
        {"overview_document", ""},
        {"resource_path", "/app/chapters/code.ui"},
        {"widget_name", "chapter_page"},
        {"source", ""},
        {"implementation_header", implementation_header},
        {"icon", kIcon},
        {"prerequisites", std::move(prerequisites)},
        {"groups", json::array()},
        {"subchapters", std::move(subchapters)},
    };
}

// A（已实现起点）→ B（已实现）、A → C（规划）、B,C → D（已实现）。
// 主干应走 A → B → D，把覆盖已实现章节最多的分叉留下来。
ChapterCatalog MakeCatalog() {
    const json source = {
        {"catalog_version", 1},
        {"categories", json::array({
            {
                {"name", "cpp"},
                {"title", "C++"},
                {"description", "测试用分类"},
                {"icon", kIcon},
                {"handbook_documents", json::array()},
                {"chapters", json::array({
                    MakeChapter("A", json::array(), json::array({
                        MakePoint("A", "a1", 2),
                        MakePoint("A", "a2", 5),
                    }), "a.hpp"),
                    MakeChapter("B", json::array({"A"}), json::array({
                        MakePoint("B", "b1"),
                    }), "b.hpp"),
                    MakeChapter("C", json::array({"A"}), json::array({
                        MakePoint("C", "c1"),
                    })),
                    MakeChapter(
                        "D", json::array({"B", "C"}), json::array({
                            MakePoint("D", "d1"),
                        }), "d.hpp"),
                })},
            },
        })},
    };
    return ChapterCatalog::from_runtime_json(source.dump());
}

const KnowledgeNode& NodeNamed(const KnowledgeGraph& graph, const string& name) {
    const auto found = std::find_if(
        graph.nodes.begin(), graph.nodes.end(),
        [&name](const KnowledgeNode& node) {
            return node.chapter_name == name;
        });
    EXPECT_NE(found, graph.nodes.end()) << name;
    return *found;
}

TEST(KnowledgeGraphTest, LayersFollowPrerequisiteDepth) {
    const auto catalog = MakeCatalog();
    const auto graph = build_knowledge_graph(catalog, "cpp", {});

    EXPECT_EQ(graph.nodes.size(), 4u);
    EXPECT_EQ(graph.layer_count, 3);
    EXPECT_EQ(NodeNamed(graph, "A").layer, 0);
    EXPECT_EQ(NodeNamed(graph, "B").layer, 1);
    EXPECT_EQ(NodeNamed(graph, "C").layer, 1);
    EXPECT_EQ(NodeNamed(graph, "D").layer, 2);
}

TEST(KnowledgeGraphTest, SlotsPartitionEachLayerInDeclarationOrder) {
    const auto graph = build_knowledge_graph(MakeCatalog(), "cpp", {});

    const auto& b = NodeNamed(graph, "B");
    const auto& c = NodeNamed(graph, "C");
    EXPECT_EQ(b.layer_size, 2);
    EXPECT_EQ(c.layer_size, 2);
    EXPECT_EQ(b.slot, 0); // B 在 athena.json 里排在 C 前面
    EXPECT_EQ(c.slot, 1);
    EXPECT_EQ(NodeNamed(graph, "A").slot, 0);
    EXPECT_EQ(NodeNamed(graph, "A").layer_size, 1);
}

TEST(KnowledgeGraphTest, EdgesPointFromPrerequisiteToDependent) {
    const auto graph = build_knowledge_graph(MakeCatalog(), "cpp", {});
    EXPECT_EQ(graph.edges.size(), 4u); // A->B, A->C, B->D, C->D

    for (const auto& edge : graph.edges) {
        EXPECT_LT(graph.nodes[edge.from].layer, graph.nodes[edge.to].layer);
    }
}

TEST(KnowledgeGraphTest, MasteryAggregatesPerChapter) {
    const auto catalog = MakeCatalog();
    // A 的两个知识点：一个 5 星、一个 3 星 → mastered 1，completion 0.8。
    const map<string, int> mastery = {
        {"cpp.A.a1", 5},
        {"cpp.A.a2", 3},
    };
    const auto graph = build_knowledge_graph(catalog, "cpp", mastery);

    const auto& a = NodeNamed(graph, "A");
    EXPECT_EQ(a.total, 2);
    EXPECT_EQ(a.mastered, 1);
    EXPECT_NEAR(a.completion, 0.8, 1e-9);
    EXPECT_EQ(a.difficulty, 4); // (2 + 5) / 2 = 3.5，四舍五入为 4。
    EXPECT_EQ(a.description, "测试章节");
    EXPECT_EQ(a.icon.name, "test");

    const auto& d = NodeNamed(graph, "D");
    EXPECT_EQ(d.mastered, 0);
    EXPECT_NEAR(d.completion, 0.0, 1e-9);
}

TEST(KnowledgeGraphTest, UnknownCategoryYieldsEmptyGraph) {
    EXPECT_TRUE(build_knowledge_graph(MakeCatalog(), "nope", {}).empty());
}

TEST(KnowledgeGraphTest, MarksImplementationAndMainPathThroughImplementedFork) {
    const auto graph = build_knowledge_graph(MakeCatalog(), "cpp", {});

    EXPECT_TRUE(NodeNamed(graph, "A").has_implementation);
    EXPECT_TRUE(NodeNamed(graph, "B").has_implementation);
    EXPECT_FALSE(NodeNamed(graph, "C").has_implementation);
    EXPECT_TRUE(NodeNamed(graph, "D").has_implementation);

    EXPECT_TRUE(NodeNamed(graph, "A").on_main_path);
    EXPECT_TRUE(NodeNamed(graph, "B").on_main_path);
    EXPECT_FALSE(NodeNamed(graph, "C").on_main_path);
    EXPECT_TRUE(NodeNamed(graph, "D").on_main_path);

    int main_edges = 0;
    for (const auto& edge : graph.edges) {
        if (!edge.on_main_path) {
            continue;
        }
        ++main_edges;
        EXPECT_TRUE(graph.nodes[edge.from].on_main_path);
        EXPECT_TRUE(graph.nodes[edge.to].on_main_path);
    }
    EXPECT_EQ(main_edges, 2); // A→B、B→D
}

} // namespace
