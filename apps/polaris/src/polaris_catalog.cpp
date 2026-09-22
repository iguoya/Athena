#include "polaris_catalog.h"

#include <QFile>
#include <QHash>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QQueue>
#include <QSet>
#include <QVector>

#include <algorithm>

namespace {

QVariantMap objectToMap(const QJsonObject& object) {
    QVariantMap map;
    for (auto it = object.begin(); it != object.end(); ++it) {
        map.insert(it.key(), it.value().toVariant());
    }
    return map;
}

QStringList stringList(const QVariantMap& map, const char* key) {
    QStringList values;
    for (const QVariant& value : map.value(key).toList()) {
        values.append(value.toString());
    }
    return values;
}

bool hasNonEmptyStrings(const QVariantMap& object, const QStringList& keys, QString* error) {
    for (const QString& key : keys) {
        if (object.value(key).toString().trimmed().isEmpty()) {
            *error = QString("缺少必填文本字段：%1").arg(key);
            return false;
        }
    }
    return true;
}

bool hasSourceRefs(const QVariantList& refs, const QSet<QString>& sourceIds, QString* error) {
    if (refs.isEmpty()) {
        *error = "缺少 source_refs";
        return false;
    }
    for (const QVariant& value : refs) {
        const QVariantMap ref = value.toMap();
        if (!hasNonEmptyStrings(ref, {"relation", "source_id", "locator"}, error)) {
            return false;
        }
        if (!sourceIds.contains(ref.value("source_id").toString())) {
            *error = QString("引用了不存在的 source_id：%1").arg(ref.value("source_id").toString());
            return false;
        }
    }
    return true;
}

struct GraphMetrics {
    int nodeWidth = 292;
    int nodeHeight = 176;
    int columnGap = 54;
    int layerGap = 86;
    int padX = 72;
    int padY = 70;
};

GraphMetrics courseGraphMetrics() {
    // 课程知识图谱沿用原 C++ 首页那张图：360 宽卡片上摊开内容 / 用途 / 难点，
    // 不压缩介绍去迁就高度；画布变高变宽靠平移缩放。
    GraphMetrics metrics;
    metrics.nodeWidth = 360;
    metrics.nodeHeight = 448;
    metrics.columnGap = 32;
    metrics.layerGap = 64;
    metrics.padX = 56;
    metrics.padY = 56;
    return metrics;
}

int priorityRank(const QString& priority) {
    if (priority == QLatin1String("essential")) return 0;
    if (priority == QLatin1String("important")) return 1;
    return 2;
}

int stageRank(const QString& stage) {
    if (stage == QLatin1String("junior")) return 0;
    if (stage == QLatin1String("intermediate")) return 1;
    return 2;
}

struct LaidOutGraph {
    QVariantList nodes;
    int width = 1280;
    int height = 720;
};

LaidOutGraph placeLayers(const QVariantList& sourceNodes, const QVector<QVector<int>>& layers,
                         const GraphMetrics& metrics) {
    LaidOutGraph graph;
    int maximumColumns = 1;
    for (const auto& layer : layers) {
        maximumColumns = std::max(maximumColumns, static_cast<int>(layer.size()));
    }
    graph.width = std::max(1280, metrics.padX * 2 + maximumColumns * metrics.nodeWidth
        + (maximumColumns - 1) * metrics.columnGap);
    graph.height = std::max(720, metrics.padY * 2 + static_cast<int>(layers.size()) * metrics.nodeHeight
        + std::max(0, static_cast<int>(layers.size()) - 1) * metrics.layerGap);

    int y = metrics.padY;
    for (int layerIndex = 0; layerIndex < layers.size(); ++layerIndex) {
        const auto& layer = layers.at(layerIndex);
        const int rowWidth = layer.size() * metrics.nodeWidth
            + std::max(0, static_cast<int>(layer.size()) - 1) * metrics.columnGap;
        int x = (graph.width - rowWidth) / 2;
        for (const int index : layer) {
            QVariantMap node = sourceNodes.at(index).toMap();
            node.insert("x", x);
            node.insert("y", y);
            node.insert("w", metrics.nodeWidth);
            node.insert("h", metrics.nodeHeight);
            node.insert("layer", layerIndex);
            graph.nodes.append(node);
            x += metrics.nodeWidth + metrics.columnGap;
        }
        y += metrics.nodeHeight + metrics.layerGap;
    }
    return graph;
}

// 强先修的布局必须稳定：同一份内容在三个平台上得到同一层和同一位置。
LaidOutGraph layoutGraph(const QVariantList& sourceNodes, const GraphMetrics& metrics) {
    QHash<QString, int> indexOf;
    for (int i = 0; i < sourceNodes.size(); ++i) {
        indexOf.insert(sourceNodes.at(i).toMap().value("id").toString(), i);
    }

    QVector<int> indegree(sourceNodes.size(), 0);
    QVector<QVector<int>> outgoing(sourceNodes.size());
    for (int to = 0; to < sourceNodes.size(); ++to) {
        for (const QString& fromId : stringList(sourceNodes.at(to).toMap(), "requires")) {
            const int from = indexOf.value(fromId, -1);
            if (from >= 0) {
                outgoing[from].append(to);
                ++indegree[to];
            }
        }
    }

    QQueue<int> ready;
    for (int i = 0; i < indegree.size(); ++i) {
        if (indegree[i] == 0) {
            ready.enqueue(i);
        }
    }

    QVector<QVector<int>> layers;
    while (!ready.isEmpty()) {
        const int count = ready.size();
        QVector<int> layer;
        for (int i = 0; i < count; ++i) {
            const int current = ready.dequeue();
            layer.append(current);
            for (const int next : outgoing[current]) {
                if (--indegree[next] == 0) {
                    ready.enqueue(next);
                }
            }
        }
        layers.append(layer);
    }

    return placeLayers(sourceNodes, layers, metrics);
}

LaidOutGraph layoutByPriority(const QVariantList& sourceNodes, const GraphMetrics& metrics) {
    QVector<QVector<int>> buckets(3);
    for (int i = 0; i < sourceNodes.size(); ++i) {
        buckets[priorityRank(sourceNodes.at(i).toMap().value("priority").toString())].append(i);
    }
    QVector<QVector<int>> layers;
    for (const auto& bucket : buckets) {
        if (!bucket.isEmpty()) {
            layers.append(bucket);
        }
    }
    return placeLayers(sourceNodes, layers, metrics);
}

// 课程图按「这一阶段该学什么」分层：初级 → 中级 → 资深。层内再按主干 / 支撑 / 台阶排，
// 避免把必要程度和阶段混成同一条轴。
LaidOutGraph layoutByStage(const QVariantList& sourceNodes, const GraphMetrics& metrics) {
    QVector<QVector<int>> buckets(3);
    for (int i = 0; i < sourceNodes.size(); ++i) {
        buckets[stageRank(sourceNodes.at(i).toMap().value("stage").toString())].append(i);
    }
    for (auto& bucket : buckets) {
        std::sort(bucket.begin(), bucket.end(), [&](int left, int right) {
            const int byPriority = priorityRank(sourceNodes.at(left).toMap().value("priority").toString())
                - priorityRank(sourceNodes.at(right).toMap().value("priority").toString());
            if (byPriority != 0) {
                return byPriority < 0;
            }
            return left < right;
        });
    }
    QVector<QVector<int>> layers;
    for (const auto& bucket : buckets) {
        if (!bucket.isEmpty()) {
            layers.append(bucket);
        }
    }
    return placeLayers(sourceNodes, layers, metrics);
}

} // namespace

PolarisCatalog::PolarisCatalog(QString root, QObject* parent)
    : QObject(parent), m_root(std::move(root)) {
    reload();
}

bool PolarisCatalog::loadDocument(QVariantMap* document, QString* error) const {
    QFile file(m_root + "/content/polaris.json");
    if (!file.open(QIODevice::ReadOnly)) {
        *error = QString("读不到图谱内容：%1").arg(file.fileName());
        return false;
    }
    QJsonParseError parseError;
    const QJsonDocument json = QJsonDocument::fromJson(file.readAll(), &parseError);
    if (parseError.error != QJsonParseError::NoError || !json.isObject()) {
        *error = QString("polaris.json 无效：%1").arg(parseError.errorString());
        return false;
    }
    *document = objectToMap(json.object());

    QFile sourceFile(m_root + "/content/sources/catalog.json");
    if (!sourceFile.open(QIODevice::ReadOnly)) {
        *error = QString("读不到来源目录：%1").arg(sourceFile.fileName());
        return false;
    }
    QJsonParseError sourceParseError;
    const QJsonDocument sourceJson = QJsonDocument::fromJson(sourceFile.readAll(), &sourceParseError);
    if (sourceParseError.error != QJsonParseError::NoError || !sourceJson.isObject()) {
        *error = QString("来源目录无效：%1").arg(sourceParseError.errorString());
        return false;
    }
    document->insert("sources", sourceJson.object().value("sources").toArray().toVariantList());
    return true;
}

bool PolarisCatalog::validateDocument(const QVariantMap& document, QString* error) const {
    if (!hasNonEmptyStrings(document, {"title", "subtitle"}, error)) {
        return false;
    }
    const QVariantList maps = document.value("maps").toList();
    if (maps.size() < 2) {
        *error = "至少需要两张地图，才能构成图谱合集。";
        return false;
    }

    QSet<QString> sourceIds;
    for (const QVariant& value : document.value("sources").toList()) {
        const QVariantMap source = value.toMap();
        if (!hasNonEmptyStrings(source, {"id", "title", "url", "kind"}, error)) {
            return false;
        }
        if (sourceIds.contains(source.value("id").toString())) {
            *error = QString("来源 ID 重复：%1").arg(source.value("id").toString());
            return false;
        }
        sourceIds.insert(source.value("id").toString());
    }
    if (sourceIds.isEmpty()) {
        *error = "来源目录不能为空。";
        return false;
    }

    // 先过一遍地图清单。节点的 targets 要指向职业目标层的地图，而校验它是否存在
    // 需要先知道每张图的 view_kind——在校验节点的同一个循环里，后面的地图还没
    // 读到。跨图关联（cross_edges）的两端校验同理，见本函数末尾。
    QHash<QString, QString> viewKindByMapId;
    for (const QVariant& mapValue : maps) {
        const QVariantMap map = mapValue.toMap();
        viewKindByMapId.insert(map.value("id").toString(),
                               map.value("view_kind").toString());
    }

    QSet<QString> mapIds;
    QSet<QString> globalNodeIds;
    QHash<QString, QString> mapIdByNodeId;
    for (const QVariant& mapValue : maps) {
        const QVariantMap map = mapValue.toMap();
        if (!hasNonEmptyStrings(map, {"id", "title", "summary", "view_kind"}, error)) {
            return false;
        }
        const QString mapId = map.value("id").toString();
        if (mapIds.contains(mapId)) {
            *error = QString("地图 ID 重复：%1").arg(mapId);
            return false;
        }
        mapIds.insert(mapId);
        const QVariantList nodes = map.value("nodes").toList();
        if (nodes.size() < 3) {
            *error = QString("地图 %1 少于三个节点，不能形成有意义的路径。").arg(mapId);
            return false;
        }

        // 不建节点的理论科目（ADR 0009 第 7 条）：它们不是可验证的实践科目，
        // 建成节点会和实践科目排成一排。可以没有，写了就要三段齐全——只给名字
        // 等于把一份课程表塞进图谱。
        for (const QVariant& value : map.value("theory").toList()) {
            const QVariantMap topic = value.toMap();
            if (!hasNonEmptyStrings(topic, {"name", "content", "role"}, error)) {
                *error = QString("地图 %1 的理论科目：%2").arg(mapId, *error);
                return false;
            }
        }

        QSet<QString> nodeIds;
        QHash<QString, QSet<QString>> requirements;
        QHash<QString, QString> nodeStage;
        for (const QVariant& nodeValue : nodes) {
            const QVariantMap node = nodeValue.toMap();
            // 技术体系层（academic）才强制必要程度与难点（ADR 0009）：那是从
            // apps/cpp 路线图吸收来、并按职业目标层反推定级的那一层。职业方向 /
            // 职业目标图另有自己的结构，不在这一次吸收里改写。
            const QString viewKind = map.value("view_kind").toString();
            const bool academic = viewKind == "academic";
            QStringList requiredFields = {"id", "title", "track", "stable_definition",
                                         "engineering_role", "practice", "validation", "volatility"};
            if (academic) {
                requiredFields << "pitfall" << "priority" << "priority_reason";
            }
            if (!hasNonEmptyStrings(node, requiredFields, error)) {
                return false;
            }
            const QString nodeId = node.value("id").toString();
            if (nodeIds.contains(nodeId) || globalNodeIds.contains(nodeId)) {
                *error = QString("节点 ID 必须全局唯一：%1").arg(nodeId);
                return false;
            }
            nodeIds.insert(nodeId);
            globalNodeIds.insert(nodeId);
            mapIdByNodeId.insert(nodeId, mapId);

            const QString validation = node.value("validation").toString();
            static const QSet<QString> knownValidation {
                "measurement", "benchmark", "integration", "review", "simulation", "analysis"
            };
            if (!knownValidation.contains(validation)) {
                *error = QString("节点 %1 的 validation 取值无效：%2").arg(nodeId, validation);
                return false;
            }
            const QString volatility = node.value("volatility").toString();
            if (volatility != "stable" && volatility != "evolving" && volatility != "volatile") {
                *error = QString("节点 %1 的 volatility 只能是 stable、evolving 或 volatile。")
                             .arg(nodeId);
                return false;
            }

            if (academic) {
                // 学习的必要程度按职业目标层的专业方向判定（ADR 0009 第 5 条）：等级、
                // 理由和它支撑的目标能力三者必须同时在场。只留等级会退化成口味排序，
                // 只留理由则无法排先后。
                const QString priority = node.value("priority").toString();
                if (priority != "essential" && priority != "important" && priority != "optional") {
                    *error = QString("节点 %1 的 priority 只能是 essential、important 或 optional。")
                                 .arg(nodeId);
                    return false;
                }
                const QString stage = node.value("stage").toString();
                if (!stage.isEmpty()) {
                    if (stage != "junior" && stage != "intermediate" && stage != "senior") {
                        *error = QString("节点 %1 的 stage 只能是 junior、intermediate 或 senior。")
                                     .arg(nodeId);
                        return false;
                    }
                    if (node.value("stage_reason").toString().trimmed().isEmpty()) {
                        *error = QString("节点 %1 缺 stage_reason：要说明这一阶段为什么学它。")
                                     .arg(nodeId);
                        return false;
                    }
                    nodeStage.insert(nodeId, stage);
                }
                const QStringList targets = stringList(node, "targets");
                if (targets.isEmpty()) {
                    *error = QString("节点 %1 缺 targets：必要程度要能追到它支撑的目标能力。")
                                 .arg(nodeId);
                    return false;
                }
                for (const QString& target : targets) {
                    if (!viewKindByMapId.contains(target)) {
                        *error = QString("节点 %1 的 targets 引用了不存在的地图 %2。")
                                     .arg(nodeId, target);
                        return false;
                    }
                    if (viewKindByMapId.value(target) != "target") {
                        *error = QString("节点 %1 的 targets 只能指向职业目标层的地图，%2 不是。")
                                     .arg(nodeId, target);
                        return false;
                    }
                }

                // 承载这个领域的独立应用（ADR 0009 第 8 条）。可以为空（规划中的方向），
                // 但写了就必须真有那个应用，否则界面上会给出一个点不开的入口。
                const QString app = node.value("app").toString();
                if (!app.isEmpty() && !QFile::exists(m_root + "/../" + app + "/app.json")) {
                    *error = QString("节点 %1 的 app 指向了不存在的应用：%2").arg(nodeId, app);
                    return false;
                }
            }
            if (map.value("graph_kind").toString() == QStringLiteral("course")) {
                // 课程知识图谱要能看见原图上的判断：从哪进、拿什么验（ADR 0010）。
                if (!node.contains("entry")) {
                    *error = QString("课程节点 %1 缺少 entry（是否为入门起点）。").arg(nodeId);
                    return false;
                }
                const QString verify = node.value("verify").toString();
                if (verify != "code" && verify != "board" && verify != "bench") {
                    *error = QString("课程节点 %1 的 verify 只能是 code、board 或 bench。")
                                 .arg(nodeId);
                    return false;
                }
                const QVariantList chapters = node.value("chapters").toList();
                if (chapters.size() < 3) {
                    *error = QString("课程节点 %1 缺少细分章节学习流程（至少三章）。")
                                 .arg(nodeId);
                    return false;
                }
                QSet<QString> chapterIds;
                QHash<QString, QSet<QString>> chapterRequires;
                for (const QVariant& chapterValue : chapters) {
                    const QVariantMap chapter = chapterValue.toMap();
                    const QString chapterId = chapter.value("id").toString();
                    if (!hasNonEmptyStrings(chapter, {"id", "title", "summary"}, error)) {
                        *error = QString("课程节点 %1 的章节：%2").arg(nodeId, *error);
                        return false;
                    }
                    if (chapterIds.contains(chapterId)) {
                        *error = QString("课程节点 %1 的章节 ID 重复：%2").arg(nodeId, chapterId);
                        return false;
                    }
                    chapterIds.insert(chapterId);
                    const QString mastery = chapter.value("mastery").toString();
                    if (mastery != "familiarity" && mastery != "usage" && mastery != "assessment") {
                        *error = QString("章节 %1 的 mastery 只能是 familiarity、usage 或 assessment（CS2013）。")
                                     .arg(chapterId);
                        return false;
                    }
                    const QString kind = chapter.value("kind").toString();
                    const bool practice = chapter.value("hands_on").toBool() || kind == "practice";
                    if (mastery != "familiarity" && !practice) {
                        *error = QString("章节 %1 是运用或评估，必须标为实践，以便和理论区隔。")
                                     .arg(chapterId);
                        return false;
                    }
                    QSet<QString> requiredChapters;
                    for (const QString& required : stringList(chapter, "requires")) {
                        requiredChapters.insert(required);
                    }
                    chapterRequires.insert(chapterId, requiredChapters);
                }
                for (auto it = chapterRequires.cbegin(); it != chapterRequires.cend(); ++it) {
                    for (const QString& required : it.value()) {
                        if (!chapterIds.contains(required)) {
                            *error = QString("章节 %1 的先修 %2 不在本课学习流程里。")
                                         .arg(it.key(), required);
                            return false;
                        }
                    }
                }
            }
            if (!hasSourceRefs(node.value("source_refs").toList(), sourceIds, error)) {
                *error = QString("节点 %1：%2").arg(nodeId, *error);
                return false;
            }
            QSet<QString> required;
            for (const QString& id : stringList(node, "requires")) {
                if (id == nodeId) {
                    *error = QString("节点 %1 不能依赖自身。").arg(nodeId);
                    return false;
                }
                required.insert(id);
            }
            requirements.insert(nodeId, required);
        }
        for (auto it = requirements.cbegin(); it != requirements.cend(); ++it) {
            for (const QString& required : it.value()) {
                if (!nodeIds.contains(required)) {
                    *error = QString("地图 %1 的强先修 %2 不在本地图内。").arg(mapId, required);
                    return false;
                }
                const QString fromStage = nodeStage.value(required);
                const QString toStage = nodeStage.value(it.key());
                if (!fromStage.isEmpty() && !toStage.isEmpty()
                    && stageRank(fromStage) > stageRank(toStage)) {
                    *error = QString("节点 %1 不能把更高阶段的 %2 当成先修。")
                                 .arg(it.key(), required);
                    return false;
                }
            }
        }

        QSet<QString> requiredEdges;
        for (const QVariant& edgeValue : map.value("edges").toList()) {
            const QVariantMap edge = edgeValue.toMap();
            if (!hasNonEmptyStrings(edge, {"from", "to", "relation", "rationale"}, error)) {
                return false;
            }
            const QString from = edge.value("from").toString();
            const QString to = edge.value("to").toString();
            if (!nodeIds.contains(from) || !nodeIds.contains(to)) {
                *error = QString("地图 %1 的边引用了不存在的节点。").arg(mapId);
                return false;
            }
            if (!hasSourceRefs(edge.value("evidence_refs").toList(), sourceIds, error)) {
                *error = QString("边 %1 → %2：%3").arg(from, to, *error);
                return false;
            }
            const QString relation = edge.value("relation").toString();
            if (relation != "requires" && relation != "enables") {
                *error = QString("边 %1 → %2 的 relation 只能是 requires 或 enables。")
                             .arg(from, to);
                return false;
            }
            if (relation == "requires") {
                requiredEdges.insert(from + "\x1f" + to);
                if (!requirements.value(to).contains(from)) {
                    *error = QString("边 %1 → %2 标为 requires，却未写入目标节点 requires。").arg(from, to);
                    return false;
                }
            } else if (requirements.value(to).contains(from)) {
                *error = QString("边 %1 → %2 是虚线来路，不应写入目标节点 requires。").arg(from, to);
                return false;
            }
        }
        for (auto it = requirements.cbegin(); it != requirements.cend(); ++it) {
            for (const QString& from : it.value()) {
                if (!requiredEdges.contains(from + "\x1f" + it.key())) {
                    *error = QString("强先修 %1 → %2 缺少带依据的 requires 边。").arg(from, it.key());
                    return false;
                }
            }
        }

        QHash<QString, int> indegree;
        QHash<QString, QStringList> outgoing;
        for (const QString& nodeId : nodeIds) {
            indegree.insert(nodeId, requirements.value(nodeId).size());
            for (const QString& required : requirements.value(nodeId)) {
                outgoing[required].append(nodeId);
            }
        }
        QQueue<QString> ready;
        for (const QString& nodeId : nodeIds) {
            if (indegree.value(nodeId) == 0) {
                ready.enqueue(nodeId);
            }
        }
        int visited = 0;
        while (!ready.isEmpty()) {
            const QString nodeId = ready.dequeue();
            ++visited;
            for (const QString& next : outgoing.value(nodeId)) {
                if (--indegree[next] == 0) {
                    ready.enqueue(next);
                }
            }
        }
        if (visited != nodeIds.size()) {
            *error = QString("地图 %1 的 requires 形成了环。").arg(mapId);
            return false;
        }
    }

    // 跨图关联（ADR 0009 第 6 条）。技术体系层拆成八张之后，「C 语言 → 51 单片机」
    // 「操作系统 → Linux 驱动」这类真实存在的先修关系两端落在不同的图里。图内
    // requires 不跨图，这些关系放顶层，拆图才不会连带丢掉依赖信息。
    QSet<QString> crossKeys;
    for (const QVariant& value : document.value("cross_edges").toList()) {
        const QVariantMap edge = value.toMap();
        if (!hasNonEmptyStrings(edge, {"from", "to", "rationale"}, error)) {
            return false;
        }
        const QString from = edge.value("from").toString();
        const QString to = edge.value("to").toString();
        if (!globalNodeIds.contains(from) || !globalNodeIds.contains(to)) {
            *error = QString("跨图关联 %1 → %2 引用了不存在的节点。").arg(from, to);
            return false;
        }
        if (mapIdByNodeId.value(from) == mapIdByNodeId.value(to)) {
            *error = QString("跨图关联 %1 → %2 的两端在同一张图里，应当写成图内 requires。")
                         .arg(from, to);
            return false;
        }
        const QString key = from + "\x1f" + to;
        if (crossKeys.contains(key)) {
            *error = QString("跨图关联重复：%1 → %2").arg(from, to);
            return false;
        }
        crossKeys.insert(key);
        if (!hasSourceRefs(edge.value("evidence_refs").toList(), sourceIds, error)) {
            *error = QString("跨图关联 %1 → %2：%3").arg(from, to, *error);
            return false;
        }
    }

    return true;
}

bool PolarisCatalog::reload() {
    const QString previouslySelectedMap = m_selected_map_id;
    const QString previouslySelectedNode = m_selected_node.value("id").toString();
    QVariantMap document;
    QString validationError;
    if (!loadDocument(&document, &validationError) || !validateDocument(document, &validationError)) {
        m_error = validationError;
        clearMap();
        emit catalogChanged();
        emit selectionChanged();
        return false;
    }

    m_error.clear();
    m_title = document.value("title").toString();
    m_subtitle = document.value("subtitle").toString();
    m_maps = document.value("maps").toList();
    m_cross_edges = document.value("cross_edges").toList();
    emit catalogChanged();

    // 默认落在第一张学科入口图上：方向图要先有学科底盘才谈得上选方向。
    QString fallbackMapId = m_maps.first().toMap().value("id").toString();
    for (const QVariant& mapValue : m_maps) {
        const QVariantMap map = mapValue.toMap();
        if (map.value("view_kind").toString() == "academic") {
            fallbackMapId = map.value("id").toString();
            break;
        }
    }
    const QString mapId = previouslySelectedMap.isEmpty() ? fallbackMapId : previouslySelectedMap;
    openMap(mapId);
    if (!previouslySelectedNode.isEmpty()) {
        selectNode(previouslySelectedNode);
    }
    return true;
}

void PolarisCatalog::clearMap() {
    m_selected_map_id.clear();
    m_selected_map_title.clear();
    m_selected_map_summary.clear();
    m_selected_map_family.clear();
    m_selected_companion_map_id.clear();
    m_selected_companion_map_title.clear();
    m_nodes.clear();
    m_edges.clear();
    m_selected_node.clear();
    m_selected_map_theory.clear();
    m_cross_edges.clear();
    m_canvas_width = 1280;
    m_canvas_height = 720;
}

void PolarisCatalog::applyMap(const QVariantMap& map) {
    m_selected_map_id = map.value("id").toString();
    m_selected_map_title = map.value("title").toString();
    m_selected_map_summary = map.value("summary").toString();
    m_selected_map_family = map.value("family").toString();
    m_selected_companion_map_id = map.value("companion_map").toString();
    m_selected_companion_map_title.clear();
    for (const QVariant& mapValue : m_maps) {
        const QVariantMap companion = mapValue.toMap();
        if (companion.value("id").toString() == m_selected_companion_map_id) {
            m_selected_companion_map_title = companion.value("title").toString();
            break;
        }
    }
    QVariantList classifiedNodes;
    const QVariantMap priorityTiers = map.value("priority_tiers").toMap();
    for (const QVariant& nodeValue : map.value("nodes").toList()) {
        QVariantMap node = nodeValue.toMap();
        for (const QString& tier : {QStringLiteral("essential"), QStringLiteral("growth"),
                                   QStringLiteral("specialist")}) {
            if (stringList(priorityTiers, tier.toUtf8().constData()).contains(node.value("id").toString())) {
                node.insert("priority_tier", tier);
                break;
            }
        }
        classifiedNodes.append(node);
    }
    const bool course = map.value("graph_kind").toString() == QStringLiteral("course");
    bool courseHasStage = false;
    if (course) {
        for (const QVariant& nodeValue : classifiedNodes) {
            if (!nodeValue.toMap().value("stage").toString().isEmpty()) {
                courseHasStage = true;
                break;
            }
        }
    }
    const LaidOutGraph laidOut = course
        ? (courseHasStage
               ? layoutByStage(classifiedNodes, courseGraphMetrics())
               : layoutByPriority(classifiedNodes, courseGraphMetrics()))
        : layoutGraph(classifiedNodes, GraphMetrics{});
    m_nodes = laidOut.nodes;
    QVariantList numberedEdges;
    int edgeNumber = 1;
    for (const QVariant& value : map.value("edges").toList()) {
        QVariantMap edge = value.toMap();
        edge.insert("number", edgeNumber++);
        numberedEdges.append(edge);
    }
    m_edges = numberedEdges;
    m_selected_map_theory = map.value("theory").toList();
    m_canvas_width = laidOut.width;
    m_canvas_height = laidOut.height;
    m_selected_node.clear();
}

bool PolarisCatalog::mapLocked(const QString& mapId) const {
    // 职业方向 / 职业目标仍在内容里，界面先锁住：当前只培养知识体系（ADR 0012）。
    for (const QVariant& mapValue : m_maps) {
        const QVariantMap map = mapValue.toMap();
        if (map.value("id").toString() == mapId) {
            return map.value("view_kind").toString() != QStringLiteral("academic");
        }
    }
    return true;
}

void PolarisCatalog::openMap(const QString& mapId) {
    for (const QVariant& mapValue : m_maps) {
        const QVariantMap map = mapValue.toMap();
        if (map.value("id").toString() == mapId) {
            applyMap(map);
            emit selectionChanged();
            return;
        }
    }
    m_error = QString("找不到地图：%1").arg(mapId);
    emit catalogChanged();
}

void PolarisCatalog::selectNode(const QString& nodeId) {
    for (const QVariant& nodeValue : m_nodes) {
        const QVariantMap node = nodeValue.toMap();
        if (node.value("id").toString() == nodeId) {
            m_selected_node = node;
            emit selectionChanged();
            return;
        }
    }
}

void PolarisCatalog::openNode(const QString& nodeId) {
    QString mapId;
    for (const QVariant& mapValue : m_maps) {
        const QVariantMap map = mapValue.toMap();
        for (const QVariant& nodeValue : map.value("nodes").toList()) {
            if (nodeValue.toMap().value("id").toString() == nodeId) {
                mapId = map.value("id").toString();
                break;
            }
        }
        if (!mapId.isEmpty()) {
            break;
        }
    }
    if (mapId.isEmpty()) {
        return;
    }
    if (mapId != m_selected_map_id) {
        openMap(mapId);
    }
    selectNode(nodeId);
}

void PolarisCatalog::clearSelection() {
    if (!m_selected_node.isEmpty()) {
        m_selected_node.clear();
        emit selectionChanged();
    }
}

QString PolarisCatalog::relationLabel(const QString& relation) const {
    if (relation == "requires") return "强先修";
    if (relation == "enables") return "能力使能";
    if (relation == "optional") return "场景选修";
    if (relation == "cross_system") return "跨系统接口";
    return relation;
}

// 课程图按培养要求分级；职业目标图仍用同一套词，表示对那个落点有多必要。
QString PolarisCatalog::priorityLabel(const QString& priority) const {
    if (priority == "essential") return "必需 · 学科核心";
    if (priority == "important") return "重要 · 实现目标";
    if (priority == "optional") return "可选 · 列出以免盲点";
    return "未分级";
}

QString PolarisCatalog::priorityBadge(const QString& priority) const {
    if (priority == "essential") return "核心";
    if (priority == "important") return "建议";
    if (priority == "optional") return "可选";
    return "未分级";
}

QString PolarisCatalog::priorityColor(const QString& priority) const {
    if (priority == "essential") return "#0F766E";
    if (priority == "important") return "#B7791F";
    if (priority == "optional") return "#7563A6";
    return "#667085";
}

QString PolarisCatalog::stageLabel(const QString& stage) const {
    if (stage == "junior") return "初级 · 这一阶段学";
    if (stage == "intermediate") return "中级 · 这一阶段学";
    if (stage == "senior") return "资深 · 这一阶段学";
    return "未分阶段";
}

QString PolarisCatalog::stageBadge(const QString& stage) const {
    if (stage == "junior") return "初级";
    if (stage == "intermediate") return "中级";
    if (stage == "senior") return "资深";
    return "未分阶段";
}

QString PolarisCatalog::stageColor(const QString& stage) const {
    if (stage == "junior") return "#2E8F7A";
    if (stage == "intermediate") return "#3D7A86";
    if (stage == "senior") return "#8A7A4A";
    return "#667085";
}

int PolarisCatalog::stageRank(const QString& stage) const {
    if (stage == "junior") return 0;
    if (stage == "intermediate") return 1;
    if (stage == "senior") return 2;
    return -1;
}

QString PolarisCatalog::previousStageBadge(const QString& stage) const {
    if (stage == "senior") return "中级";
    if (stage == "intermediate") return "初级";
    return QString();
}

QString PolarisCatalog::chapterMasteryLabel(const QString& mastery) const {
    if (mastery == "familiarity") return "熟悉";
    if (mastery == "usage") return "运用";
    if (mastery == "assessment") return "评估";
    return "未分级";
}

QString PolarisCatalog::chapterMasteryHint(const QString& mastery) const {
    if (mastery == "familiarity") return "能指认这个概念，知道它解决什么";
    if (mastery == "usage") return "能在常规情境里动手做";
    if (mastery == "assessment") return "能比较方案、判断边界和失效";
    return QString();
}

QString PolarisCatalog::chapterMasteryColor(const QString& mastery) const {
    if (mastery == "familiarity") return "#8A7A4A";
    if (mastery == "usage") return "#3D7A86";
    if (mastery == "assessment") return "#2E8F7A";
    return "#667085";
}

QVariantList PolarisCatalog::crossEdgesFor(const QString& nodeId) const {
    QVariantList related;
    for (const QVariant& value : m_cross_edges) {
        const QVariantMap edge = value.toMap();
        const QString from = edge.value("from").toString();
        const QString to = edge.value("to").toString();
        const bool incoming = to == nodeId;
        if (!incoming && from != nodeId) {
            continue;
        }
        const QString peerId = incoming ? from : to;
        QVariantMap item;
        item.insert("peer_id", peerId);
        // incoming：对端是本节点的前置；否则本节点是对端的前置。
        item.insert("incoming", incoming);
        item.insert("strong", edge.value("strong", true));
        item.insert("rationale", edge.value("rationale"));
        item.insert("peer_title", peerId);
        for (const QVariant& mapValue : m_maps) {
            const QVariantMap map = mapValue.toMap();
            bool found = false;
            for (const QVariant& nodeValue : map.value("nodes").toList()) {
                const QVariantMap node = nodeValue.toMap();
                if (node.value("id").toString() != peerId) {
                    continue;
                }
                item.insert("peer_title", node.value("title"));
                item.insert("map_id", map.value("id"));
                item.insert("map_title", map.value("title"));
                found = true;
                break;
            }
            if (found) {
                break;
            }
        }
        related.append(item);
    }
    return related;
}

QString PolarisCatalog::mapTitle(const QString& mapId) const {
    for (const QVariant& value : m_maps) {
        const QVariantMap map = value.toMap();
        if (map.value("id").toString() == mapId) {
            return map.value("title").toString();
        }
    }
    return mapId;
}

QString PolarisCatalog::nodeTitle(const QString& nodeId) const {
    for (const QVariant& value : m_nodes) {
        const QVariantMap node = value.toMap();
        if (node.value("id").toString() == nodeId) {
            return node.value("title").toString();
        }
    }
    return nodeId;
}

QString PolarisCatalog::volatilityLabel(const QString& volatility) const {
    if (volatility == "stable") return "稳定基础";
    if (volatility == "evolving") return "持续演进";
    if (volatility == "volatile") return "快速变化";
    return volatility;
}

QString PolarisCatalog::validationLabel(const QString& validation) const {
    if (validation == "analysis") return "分析 / 推导";
    if (validation == "measurement") return "测量 / 标定";
    if (validation == "benchmark") return "基准 / 剖析";
    if (validation == "integration") return "集成 / 接口";
    if (validation == "simulation") return "仿真 / SIL / HIL";
    if (validation == "review") return "评审 / 追溯";
    return validation;
}

QString PolarisCatalog::verifyLabel(const QString& verify) const {
    if (verify == "code") return "编程";
    if (verify == "board") return "开发板";
    if (verify == "bench") return "硬件";
    return verify;
}

QString PolarisCatalog::trackLabel(const QString& track) const {
    if (track == "language") return "编程语言";
    if (track == "engineering") return "结构与工程";
    if (track == "systems") return "系统";
    if (track == "hardware") return "电路与嵌入式";
    if (track == "ai") return "模型与端侧";
    if (track == "capstone") return "综合应用";
    if (track == "foundation") return "基础";
    if (track == "software") return "软件";
    if (track == "electronics") return "电子";
    if (track == "control") return "控制";
    if (track == "compute") return "计算";
    if (track == "assurance") return "保障";
    return track;
}

QString PolarisCatalog::trackColor(const QString& track) const {
    if (track == "language") return "#4969A8";
    if (track == "engineering") return "#2E6F78";
    if (track == "systems") return "#3B5B8A";
    if (track == "hardware") return "#9A6632";
    if (track == "ai") return "#3B7E64";
    if (track == "capstone") return "#A2464B";
    if (track == "foundation") return "#2E6F78";
    if (track == "software") return "#4969A8";
    if (track == "electronics") return "#9A6632";
    if (track == "control") return "#8A557E";
    if (track == "compute") return "#3B7E64";
    if (track == "assurance") return "#A2464B";
    return "#667085";
}

QString PolarisCatalog::familyLabel(const QString& family) const {
    if (family == "system") return "体系地图";
    if (family == "playbook") return "实操地图";
    return family;
}
