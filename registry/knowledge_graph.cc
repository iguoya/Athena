#include "registry/knowledge_graph.h"

#include "registry/progress_stats.h"

#include <algorithm>
#include <cmath>

namespace {

// 记忆化 + 在途标记求每个章节的层号：layer(n) = 0（无前置）或所有前置层
// 号最大值 + 1。visiting 命中说明遇到环（生成器本应拦下），按 0 兜底。
int resolve_layer(
    int index,
    const vector<vector<int>>& prerequisites,
    vector<int>& layer_cache,
    vector<char>& visiting) {
    if (layer_cache[index] >= 0) {
        return layer_cache[index];
    }
    if (visiting[index]) {
        return 0;
    }
    visiting[index] = 1;
    int layer = 0;
    for (const int prerequisite : prerequisites[index]) {
        layer = max(
            layer,
            resolve_layer(prerequisite, prerequisites, layer_cache, visiting)
                + 1);
    }
    visiting[index] = 0;
    layer_cache[index] = layer;
    return layer;
}

// 子树内（含自身）已实现章节数；用于从分叉处选出覆盖实现最多的主干后继。
int count_implemented_reachable(
    int index,
    const vector<vector<int>>& successors,
    const vector<char>& has_implementation,
    vector<int>& cache,
    vector<char>& visiting) {
    if (cache[index] >= 0) {
        return cache[index];
    }
    if (visiting[index]) {
        return 0;
    }
    visiting[index] = 1;
    int total = has_implementation[index] ? 1 : 0;
    for (const int next : successors[index]) {
        total += count_implemented_reachable(
            next, successors, has_implementation, cache, visiting);
    }
    visiting[index] = 0;
    cache[index] = total;
    return total;
}

void mark_main_path(
    const vector<vector<int>>& successors,
    const vector<char>& has_implementation,
    vector<char>& node_on_path,
    vector<vector<char>>& edge_on_path) {
    const int n = static_cast<int>(successors.size());
    if (n == 0) {
        return;
    }

    vector<int> impl_reachable(static_cast<size_t>(n), -1);
    vector<char> visiting(static_cast<size_t>(n), 0);
    for (int i = 0; i < n; ++i) {
        count_implemented_reachable(
            i, successors, has_implementation, impl_reachable, visiting);
    }

    // 从入度为 0 的起点里选覆盖已实现章节最多的；没有独立起点时退回全图最大。
    vector<int> indegree(static_cast<size_t>(n), 0);
    for (int i = 0; i < n; ++i) {
        for (const int next : successors[static_cast<size_t>(i)]) {
            ++indegree[static_cast<size_t>(next)];
        }
    }
    auto better_start = [&](int candidate, int incumbent) {
        if (incumbent < 0) {
            return true;
        }
        if (impl_reachable[candidate] != impl_reachable[incumbent]) {
            return impl_reachable[candidate] > impl_reachable[incumbent];
        }
        return candidate < incumbent;
    };
    int current = -1;
    for (int i = 0; i < n; ++i) {
        if (indegree[static_cast<size_t>(i)] == 0 && better_start(i, current)) {
            current = i;
        }
    }
    if (current < 0) {
        current = 0;
        for (int i = 1; i < n; ++i) {
            if (better_start(i, current)) {
                current = i;
            }
        }
    }

    vector<char> seen(static_cast<size_t>(n), 0);
    while (current >= 0 && !seen[static_cast<size_t>(current)]) {
        seen[static_cast<size_t>(current)] = 1;
        node_on_path[static_cast<size_t>(current)] = 1;

        int best = -1;
        for (const int next : successors[static_cast<size_t>(current)]) {
            if (best < 0
                || impl_reachable[next] > impl_reachable[best]
                || (impl_reachable[next] == impl_reachable[best]
                    && next < best)) {
                best = next;
            }
        }
        if (best < 0) {
            break;
        }
        edge_on_path[static_cast<size_t>(current)][static_cast<size_t>(best)] =
            1;
        current = best;
    }
}

} // namespace

KnowledgeGraph build_knowledge_graph(
    const ChapterCatalog& catalog,
    const string& category_name,
    const map<string, int>& mastery_by_id) {
    KnowledgeGraph graph;

    const auto category = catalog.chapters().find(category_name);
    if (category == catalog.chapters().end() || category->second.empty()) {
        return graph;
    }
    const auto& chapters = category->second;

    map<string, int> index_by_name;
    for (size_t i = 0; i < chapters.size(); ++i) {
        index_by_name[chapters[i].name] = static_cast<int>(i);
    }

    vector<vector<int>> prerequisites(chapters.size());
    vector<vector<int>> successors(chapters.size());
    for (size_t i = 0; i < chapters.size(); ++i) {
        for (const auto& name : chapters[i].prerequisites) {
            const auto found = index_by_name.find(name);
            if (found != index_by_name.end()) {
                prerequisites[i].push_back(found->second);
                successors[static_cast<size_t>(found->second)].push_back(
                    static_cast<int>(i));
            }
        }
    }

    vector<int> layer_cache(chapters.size(), -1);
    vector<char> visiting(chapters.size(), 0);
    for (size_t i = 0; i < chapters.size(); ++i) {
        resolve_layer(
            static_cast<int>(i), prerequisites, layer_cache, visiting);
    }

    int layer_count = 0;
    for (const int layer : layer_cache) {
        layer_count = max(layer_count, layer + 1);
    }
    graph.layer_count = layer_count;

    vector<int> filled_per_layer(static_cast<size_t>(layer_count), 0);
    vector<int> layer_totals(static_cast<size_t>(layer_count), 0);
    for (const int layer : layer_cache) {
        ++layer_totals[static_cast<size_t>(layer)];
    }

    vector<char> has_implementation(chapters.size(), 0);
    for (size_t i = 0; i < chapters.size(); ++i) {
        has_implementation[i] =
            chapters[i].implementation_header.empty() ? 0 : 1;
    }

    vector<char> node_on_path(chapters.size(), 0);
    vector<vector<char>> edge_on_path(
        chapters.size(), vector<char>(chapters.size(), 0));
    mark_main_path(successors, has_implementation, node_on_path, edge_on_path);

    graph.nodes.reserve(chapters.size());
    for (size_t i = 0; i < chapters.size(); ++i) {
        const auto& chapter = chapters[i];
        const int layer = layer_cache[i];

        int mastery_sum = 0;
        int mastered = 0;
        int difficulty_sum = 0;
        int difficulty_count = 0;
        for (const auto& subchapter : chapter.subchapters) {
            int mastery = 0;
            const auto record = mastery_by_id.find(subchapter.function_id);
            if (record != mastery_by_id.end()) {
                mastery = record->second;
            }
            mastery_sum += mastery;
            if (mastery >= kMaxMastery) {
                ++mastered;
            }
            if (subchapter.difficulty > 0) {
                difficulty_sum += subchapter.difficulty;
                ++difficulty_count;
            }
        }
        const int total = static_cast<int>(chapter.subchapters.size());
        const double completion =
            total > 0 ? mastery_sum / (static_cast<double>(kMaxMastery) * total)
                      : 0.0;

        graph.nodes.push_back({
            .chapter_name = chapter.name,
            .title = chapter.title,
            .description = chapter.description,
            .icon = chapter.icon,
            .layer = layer,
            .slot = filled_per_layer[static_cast<size_t>(layer)]++,
            .layer_size = layer_totals[static_cast<size_t>(layer)],
            .total = total,
            .mastered = mastered,
            .difficulty = difficulty_count > 0
                ? static_cast<int>(lround(
                      difficulty_sum / static_cast<double>(difficulty_count)))
                : 0,
            .completion = completion,
            .has_implementation = has_implementation[i] != 0,
            .on_main_path = node_on_path[i] != 0,
        });
    }

    for (size_t i = 0; i < chapters.size(); ++i) {
        for (const int prerequisite : prerequisites[i]) {
            graph.edges.push_back({
                .from = prerequisite,
                .to = static_cast<int>(i),
                .on_main_path =
                    edge_on_path[static_cast<size_t>(prerequisite)][i] != 0,
            });
        }
    }

    return graph;
}
