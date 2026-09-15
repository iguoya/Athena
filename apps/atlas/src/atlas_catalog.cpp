#include "atlas_catalog.h"

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

struct LaidOutGraph {
    QVariantList nodes;
    int width = 1280;
    int height = 720;
};

// 强先修的布局必须稳定：同一份内容在三个平台上得到同一层和同一位置。
LaidOutGraph layoutGraph(const QVariantList& sourceNodes, const GraphMetrics& metrics) {
    LaidOutGraph graph;
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

} // namespace

AtlasCatalog::AtlasCatalog(QString root, QObject* parent)
    : QObject(parent), m_root(std::move(root)) {
    reload();
}

bool AtlasCatalog::loadDocument(QVariantMap* document, QString* error) const {
    QFile file(m_root + "/content/atlas.json");
    if (!file.open(QIODevice::ReadOnly)) {
        *error = QString("读不到图谱内容：%1").arg(file.fileName());
        return false;
    }
    QJsonParseError parseError;
    const QJsonDocument json = QJsonDocument::fromJson(file.readAll(), &parseError);
    if (parseError.error != QJsonParseError::NoError || !json.isObject()) {
        *error = QString("atlas.json 无效：%1").arg(parseError.errorString());
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

bool AtlasCatalog::validateDocument(const QVariantMap& document, QString* error) const {
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

    QSet<QString> mapIds;
    QSet<QString> globalNodeIds;
    for (const QVariant& mapValue : maps) {
        const QVariantMap map = mapValue.toMap();
        if (!hasNonEmptyStrings(map, {"id", "title", "summary", "view_kind", "family", "companion_map", "emphasis"}, error)) {
            return false;
        }
        const QString family = map.value("family").toString();
        if (family != "system" && family != "playbook") {
            *error = QString("地图 %1 的 family 只能是 system 或 playbook。").arg(map.value("id").toString());
            return false;
        }
        const QString emphasis = map.value("emphasis").toString();
        if (emphasis != "trunk" && emphasis != "support" && emphasis != "reference"
            && emphasis != "adjacent") {
            *error = QString("地图 %1 的 emphasis 只能是 trunk、support、reference 或 adjacent。")
                         .arg(map.value("id").toString());
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

        QSet<QString> nodeIds;
        QHash<QString, QSet<QString>> requirements;
        for (const QVariant& nodeValue : nodes) {
            const QVariantMap node = nodeValue.toMap();
            if (!hasNonEmptyStrings(node, {"id", "title", "track", "stable_definition",
                                         "engineering_role", "practice", "validation", "volatility"}, error)) {
                return false;
            }
            const QString nodeId = node.value("id").toString();
            if (nodeIds.contains(nodeId) || globalNodeIds.contains(nodeId)) {
                *error = QString("节点 ID 必须全局唯一：%1").arg(nodeId);
                return false;
            }
            nodeIds.insert(nodeId);
            globalNodeIds.insert(nodeId);
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
            }
        }

        // 学习取舍不是视觉标签：每个节点必须且只能属于一个投入优先级。
        const QVariantMap priorityTiers = map.value("priority_tiers").toMap();
        const QStringList knownTiers {"essential", "growth", "specialist"};
        QSet<QString> classified;
        for (const QString& tier : knownTiers) {
            for (const QString& nodeId : stringList(priorityTiers, tier.toUtf8().constData())) {
                if (!nodeIds.contains(nodeId)) {
                    *error = QString("地图 %1 的优先级 %2 引用了不存在节点 %3。")
                        .arg(mapId, tier, nodeId);
                    return false;
                }
                if (classified.contains(nodeId)) {
                    *error = QString("地图 %1 的节点 %2 被重复划入优先级。").arg(mapId, nodeId);
                    return false;
                }
                classified.insert(nodeId);
            }
        }
        if (classified != nodeIds) {
            *error = QString("地图 %1 的 priority_tiers 必须完整划分全部节点。").arg(mapId);
            return false;
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
            if (edge.value("relation").toString() == "requires") {
                requiredEdges.insert(from + "\x1f" + to);
                if (!requirements.value(to).contains(from)) {
                    *error = QString("边 %1 → %2 标为 requires，却未写入目标节点 requires。").arg(from, to);
                    return false;
                }
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

    QHash<QString, QString> mapFamily;
    QHash<QString, QString> companionOf;
    QHash<QString, QString> nodeFamily;
    QHash<QString, QString> mapEmphasis;
    for (const QVariant& mapValue : maps) {
        const QVariantMap map = mapValue.toMap();
        const QString mapId = map.value("id").toString();
        const QString family = map.value("family").toString();
        mapFamily.insert(mapId, family);
        mapEmphasis.insert(mapId, map.value("emphasis").toString());
        companionOf.insert(mapId, map.value("companion_map").toString());
        for (const QVariant& nodeValue : map.value("nodes").toList()) {
            nodeFamily.insert(nodeValue.toMap().value("id").toString(), family);
        }
    }
    if (!mapFamily.values().contains("system") || !mapFamily.values().contains("playbook")) {
        *error = "体系地图与实操地图必须同时存在。";
        return false;
    }
    for (auto it = companionOf.cbegin(); it != companionOf.cend(); ++it) {
        if (!mapIds.contains(it.value())) {
            *error = QString("地图 %1 的 companion_map 不存在：%2").arg(it.key(), it.value());
            return false;
        }
        if (companionOf.value(it.value()) != it.key()) {
            *error = QString("地图 %1 与 %2 的 companion_map 必须成对互指。").arg(it.key(), it.value());
            return false;
        }
        if (mapFamily.value(it.key()) == mapFamily.value(it.value())) {
            *error = QString("地图 %1 的 companion_map 必须指向另一类地图。").arg(it.key());
            return false;
        }
        if (mapEmphasis.value(it.key()) != mapEmphasis.value(it.value())) {
            *error = QString("地图 %1 与其配对图的 emphasis 必须一致。").arg(it.key());
            return false;
        }
    }

    for (const QVariant& mapValue : maps) {
        const QVariantMap map = mapValue.toMap();
        const QString family = map.value("family").toString();
        for (const QVariant& nodeValue : map.value("nodes").toList()) {
            const QVariantMap node = nodeValue.toMap();
            const QString nodeId = node.value("id").toString();
            const QVariantMap kit = node.value("kit").toMap();
            const QStringList orients = stringList(node, "orients");
            if (family == "system") {
                if (!kit.isEmpty() || !orients.isEmpty()) {
                    *error = QString("体系节点 %1 不得携带 kit 或 orients。").arg(nodeId);
                    return false;
                }
                continue;
            }
            if (!hasNonEmptyStrings(kit, {"reading", "tooling", "artifact"}, error)) {
                *error = QString("实操节点 %1：%2").arg(nodeId, *error);
                return false;
            }
            if (orients.isEmpty()) {
                *error = QString("实操节点 %1 必须用 orients 指向至少一个体系节点。").arg(nodeId);
                return false;
            }
            for (const QString& target : orients) {
                if (!globalNodeIds.contains(target)) {
                    *error = QString("实操节点 %1 的 orients 引用了不存在的节点 %2。").arg(nodeId, target);
                    return false;
                }
                if (nodeFamily.value(target) != "system") {
                    *error = QString("实操节点 %1 只能指向体系节点，不能指向 %2。").arg(nodeId, target);
                    return false;
                }
            }
        }
    }
    return true;
}

bool AtlasCatalog::reload() {
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
    emit catalogChanged();

    QString fallbackMapId = m_maps.first().toMap().value("id").toString();
    for (const QVariant& mapValue : m_maps) {
        const QVariantMap map = mapValue.toMap();
        if (map.value("family").toString() == "system" && map.value("emphasis").toString() == "trunk") {
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

void AtlasCatalog::clearMap() {
    m_selected_map_id.clear();
    m_selected_map_title.clear();
    m_selected_map_summary.clear();
    m_selected_map_family.clear();
    m_selected_companion_map_id.clear();
    m_selected_companion_map_title.clear();
    m_nodes.clear();
    m_edges.clear();
    m_selected_node.clear();
    m_canvas_width = 1280;
    m_canvas_height = 720;
}

void AtlasCatalog::applyMap(const QVariantMap& map) {
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
    const LaidOutGraph laidOut = layoutGraph(classifiedNodes, {});
    m_nodes = laidOut.nodes;
    m_edges = map.value("edges").toList();
    m_canvas_width = laidOut.width;
    m_canvas_height = laidOut.height;
    m_selected_node.clear();
}

void AtlasCatalog::openMap(const QString& mapId) {
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

void AtlasCatalog::selectNode(const QString& nodeId) {
    for (const QVariant& nodeValue : m_nodes) {
        const QVariantMap node = nodeValue.toMap();
        if (node.value("id").toString() == nodeId) {
            m_selected_node = node;
            emit selectionChanged();
            return;
        }
    }
}

void AtlasCatalog::clearSelection() {
    if (!m_selected_node.isEmpty()) {
        m_selected_node.clear();
        emit selectionChanged();
    }
}

QString AtlasCatalog::relationLabel(const QString& relation) const {
    if (relation == "requires") return "强先修";
    if (relation == "enables") return "能力使能";
    if (relation == "optional") return "场景选修";
    if (relation == "cross_system") return "跨系统接口";
    return relation;
}

QString AtlasCatalog::priorityLabel(const QString& priorityTier) const {
    if (priorityTier == "essential") return "大众必备主干";
    if (priorityTier == "growth") return "热门 · 增长方向";
    if (priorityTier == "specialist") return "小众 · 专题参考";
    return "未分类";
}

QString AtlasCatalog::priorityColor(const QString& priorityTier) const {
    if (priorityTier == "essential") return "#0F766E";
    if (priorityTier == "growth") return "#B7791F";
    if (priorityTier == "specialist") return "#7563A6";
    return "#667085";
}

QString AtlasCatalog::volatilityLabel(const QString& volatility) const {
    if (volatility == "stable") return "稳定基础";
    if (volatility == "evolving") return "持续演进";
    if (volatility == "volatile") return "快速变化";
    return volatility;
}

QString AtlasCatalog::validationLabel(const QString& validation) const {
    if (validation == "analysis") return "分析 / 推导";
    if (validation == "measurement") return "测量 / 标定";
    if (validation == "benchmark") return "基准 / 剖析";
    if (validation == "integration") return "集成 / 接口";
    if (validation == "simulation") return "仿真 / SIL / HIL";
    if (validation == "review") return "评审 / 追溯";
    return validation;
}

QString AtlasCatalog::trackColor(const QString& track) const {
    if (track == "foundation") return "#2E6F78";
    if (track == "software") return "#4969A8";
    if (track == "electronics") return "#9A6632";
    if (track == "control") return "#8A557E";
    if (track == "compute") return "#3B7E64";
    if (track == "assurance") return "#A2464B";
    return "#667085";
}

QString AtlasCatalog::familyLabel(const QString& family) const {
    if (family == "system") return "体系地图";
    if (family == "playbook") return "实操地图";
    return family;
}
