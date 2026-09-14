#include "curriculum.h"

#include <QFile>
#include <QFileInfo>
#include <QHash>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QQueue>
#include <QSet>
#include <QVector>
#include <algorithm>

using namespace std;

namespace {

struct GraphMetrics {
    int node_width = 300;
    int node_height = 152;
    int column_gap = 36;
    int layer_gap = 72;
    int pad_x = 48;
    int pad_y = 28;
};

QVariantMap object_to_map(const QJsonObject& object) {
    QVariantMap map;
    for (auto it = object.begin(); it != object.end(); ++it) {
        map.insert(it.key(), it.value().toVariant());
    }
    return map;
}

QStringList string_list(const QVariantMap& object, const char* key) {
    QStringList ids;
    for (const QVariant& value : object.value(key).toList()) {
        ids.push_back(value.toString());
    }
    return ids;
}

bool topic_openable(const QVariantMap& topic) {
    return !topic.value("qml").toString().isEmpty()
        && !topic.value("planned").toBool();
}

int chapter_open_count(const QVariantMap& chapter) {
    int count = 0;
    for (const QVariant& topic_value : chapter.value("topics").toList()) {
        if (topic_openable(topic_value.toMap())) {
            ++count;
        }
    }
    return count;
}

struct LaidOutGraph {
    QVariantList nodes;
    QVariantList edges;
    int width = 0;
    int height = 0;
};

LaidOutGraph layout_graph(
    const QVariantList& items,
    const GraphMetrics& metrics,
    const char* id_key,
    const char* requires_key) {
    LaidOutGraph graph;
    QHash<QString, int> index_of;
    for (int index = 0; index < items.size(); ++index) {
        index_of.insert(items[index].toMap().value(id_key).toString(), index);
    }

    QVector<int> indegree(items.size(), 0);
    QVector<QVector<int>> outgoing(items.size());
    for (int index = 0; index < items.size(); ++index) {
        for (const QString& required : string_list(items[index].toMap(), requires_key)) {
            if (!index_of.contains(required)) {
                continue;
            }
            const int from = index_of.value(required);
            outgoing[from].push_back(index);
            indegree[index] += 1;
        }
    }

    QQueue<int> ready;
    for (int index = 0; index < indegree.size(); ++index) {
        if (indegree[index] == 0) {
            ready.enqueue(index);
        }
    }

    QVector<QVector<int>> layers;
    QSet<int> placed;
    while (!ready.isEmpty()) {
        QVector<int> layer;
        const int count = ready.size();
        for (int step = 0; step < count; ++step) {
            const int index = ready.dequeue();
            if (placed.contains(index)) {
                continue;
            }
            placed.insert(index);
            layer.push_back(index);
            for (int next : outgoing[index]) {
                indegree[next] -= 1;
                if (indegree[next] == 0) {
                    ready.enqueue(next);
                }
            }
        }
        if (!layer.isEmpty()) {
            layers.push_back(layer);
        }
    }

    int max_cols = 1;
    for (const auto& layer : layers) {
        max_cols = std::max(max_cols, static_cast<int>(layer.size()));
    }
    graph.width = metrics.pad_x * 2
        + max_cols * metrics.node_width
        + (max_cols - 1) * metrics.column_gap;
    graph.height = metrics.pad_y * 2
        + static_cast<int>(layers.size()) * metrics.node_height
        + std::max(0, static_cast<int>(layers.size()) - 1) * metrics.layer_gap;

    QHash<QString, QVariantMap> placed_nodes;
    int y = metrics.pad_y;
    for (int layer_index = 0; layer_index < layers.size(); ++layer_index) {
        const auto& layer = layers[layer_index];
        const int count = static_cast<int>(layer.size());
        const int row_width =
            count * metrics.node_width + (count - 1) * metrics.column_gap;
        int x = (graph.width - row_width) / 2;
        for (int slot = 0; slot < count; ++slot) {
            QVariantMap node = items[layer[slot]].toMap();
            node["x"] = x;
            node["y"] = y;
            node["w"] = metrics.node_width;
            node["h"] = metrics.node_height;
            node["layer"] = layer_index;
            graph.nodes.push_back(node);
            placed_nodes.insert(node.value(id_key).toString(), node);
            x += metrics.node_width + metrics.column_gap;
        }
        y += metrics.node_height + metrics.layer_gap;
    }

    for (const auto& item_value : items) {
        const QVariantMap item = item_value.toMap();
        const QString to_id = item.value(id_key).toString();
        if (!placed_nodes.contains(to_id)) {
            continue;
        }
        const QVariantMap to = placed_nodes.value(to_id);
        for (const QString& from_id : string_list(item, requires_key)) {
            if (!placed_nodes.contains(from_id)) {
                continue;
            }
            const QVariantMap from = placed_nodes.value(from_id);
            QVariantMap edge;
            edge["from"] = from_id;
            edge["to"] = to_id;
            edge["x0"] = from.value("x").toInt() + metrics.node_width / 2;
            edge["y0"] = from.value("y").toInt() + metrics.node_height;
            edge["x1"] = to.value("x").toInt() + metrics.node_width / 2;
            edge["y1"] = to.value("y").toInt();
            graph.edges.push_back(edge);
        }
    }
    return graph;
}

} // namespace

Curriculum::Curriculum(QString root, QObject* parent)
    : QObject(parent), m_root(std::move(root)) {
    reload();
}

int Curriculum::pageIndex() const {
    switch (m_page) {
    case Page::Outline:
        return 1;
    case Page::Lesson:
        return 2;
    case Page::Home:
    default:
        return 0;
    }
}

void Curriculum::reload() {
    const QString keep_chapter = m_chapter_id;
    const QString keep_topic = m_selected_id;
    const Page keep_page = m_page;

    m_error.clear();
    m_title.clear();
    m_tagline.clear();
    m_chapters.clear();
    m_graph_nodes.clear();
    m_graph_edges.clear();
    m_chapter = {};
    m_topics.clear();
    m_topic_nodes.clear();
    m_topic_edges.clear();

    const QString path = m_root + "/content/curriculum.json";
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly)) {
        m_error = QString("读不到课表：%1").arg(path);
        emit catalogChanged();
        emit selectionChanged();
        return;
    }

    QJsonParseError parse_error;
    const QJsonDocument document = QJsonDocument::fromJson(file.readAll(), &parse_error);
    if (parse_error.error != QJsonParseError::NoError || !document.isObject()) {
        m_error = QString("课表 JSON 无效：%1").arg(parse_error.errorString());
        emit catalogChanged();
        return;
    }

    const QJsonObject root = document.object();
    m_title = root.value("title").toString("C 语言编程");
    m_tagline = root.value("tagline").toString();

    const QJsonArray chapters = root.value("chapters").toArray();
    if (chapters.isEmpty()) {
        m_error = "课表里没有章节。";
        emit catalogChanged();
        return;
    }

    for (const auto& chapter_value : chapters) {
        m_chapters.push_back(object_to_map(chapter_value.toObject()));
    }
    rebuild_chapter_graph();
    emit catalogChanged();

    if (keep_page == Page::Lesson && !keep_topic.isEmpty()) {
        set_chapter_by_id(keep_chapter);
        rebuild_topic_graph();
        select(keep_topic);
    } else if (keep_page == Page::Outline && !keep_chapter.isEmpty()) {
        openChapter(keep_chapter);
    } else {
        goHome();
    }
}

void Curriculum::goHome() {
    m_page = Page::Home;
    m_chapter_id.clear();
    m_chapter = {};
    m_topics.clear();
    m_topic_nodes.clear();
    m_topic_edges.clear();
    m_selected_id.clear();
    m_selected_topic = {};
    m_lesson_source = QUrl();
    clear_lab_message();
    emit selectionChanged();
}

void Curriculum::openChapter(const QString& chapter_id) {
    set_chapter_by_id(chapter_id);
    if (m_chapter.isEmpty()) {
        m_lab_message = "课表里没有这一章。";
        emit labMessageChanged();
        return;
    }
    rebuild_topic_graph();
    m_page = Page::Outline;
    m_selected_id.clear();
    m_selected_topic = {};
    m_lesson_source = QUrl();
    clear_lab_message();
    emit selectionChanged();
}

void Curriculum::openOutline() {
    if (m_chapter_id.isEmpty()) {
        m_lab_message = "先从知识图谱点进一章。";
        emit labMessageChanged();
        return;
    }
    openChapter(m_chapter_id);
}

void Curriculum::select(const QString& topic_id) {
    for (const auto& topic_value : m_topics) {
        const QVariantMap topic = topic_value.toMap();
        if (topic.value("id").toString() != topic_id) {
            continue;
        }
        if (!topic_openable(topic)) {
            m_lab_message = "这一节还在规划中，先点已经写成的知识点。";
            emit labMessageChanged();
            return;
        }
        clear_lab_message();
        m_page = Page::Lesson;
        m_selected_id = topic_id;
        m_selected_topic = topic;
        m_lesson_source =
            QUrl::fromLocalFile(m_root + "/qml/" + topic.value("qml").toString());
        emit selectionChanged();
        return;
    }
}

QString Curriculum::difficultyColor(int difficulty) const {
    switch (difficulty) {
    case 1:
        return "#198754";
    case 2:
        return "#0f766e";
    case 3:
        return "#b7791f";
    case 4:
        return "#fd7e14";
    case 5:
        return "#dc3545";
    default:
        return "#adb5bd";
    }
}

QString Curriculum::goalLabel(const QString& goal) const {
    if (goal == "master") {
        return "掌握";
    }
    if (goal == "required") {
        return "必须掌握";
    }
    if (goal == "familiar") {
        return "一般了解";
    }
    return "未评";
}

void Curriculum::launchLab() {
    const QString path = m_root + "/playground/build/athena-c";
    if (!QFileInfo::exists(path) || !QFileInfo(path).isExecutable()) {
        m_lab_message =
            "内存小程序还没构建。在 apps/c/playground 里 cmake 之后再开实验台。";
        emit labMessageChanged();
        return;
    }
    clear_lab_message();
    QProcess::startDetached(path, {}, m_root + "/playground");
}

void Curriculum::rebuild_chapter_graph() {
    QVariantList nodes;
    for (const auto& chapter_value : m_chapters) {
        QVariantMap chapter = chapter_value.toMap();
        const QVariantList topics = chapter.value("topics").toList();
        const int open_count = chapter_open_count(chapter);
        QVariantList point_titles;
        for (const QVariant& topic_value : topics) {
            const QVariantMap topic = topic_value.toMap();
            QVariantMap row;
            row["title"] = topic.value("title");
            row["openable"] = topic_openable(topic);
            point_titles.push_back(row);
        }
        chapter["topic_count"] = topics.size();
        chapter["open_count"] = open_count;
        chapter["planned"] = open_count == 0;
        chapter["openable"] = true;
        chapter["points"] = point_titles;
        nodes.push_back(chapter);
    }

    const LaidOutGraph laid = layout_graph(
        nodes,
        GraphMetrics{
            .node_width = 400,
            .node_height = 420,
            .column_gap = 36,
            .layer_gap = 72,
            .pad_x = 48,
            .pad_y = 28},
        "id",
        "prerequisites");
    m_graph_nodes = laid.nodes;
    m_graph_edges = laid.edges;
    m_graph_width = laid.width;
    m_graph_height = laid.height;
}

void Curriculum::rebuild_topic_graph() {
    const LaidOutGraph laid = layout_graph(
        m_topics,
        GraphMetrics{
            .node_width = 300,
            .node_height = 140,
            .column_gap = 24,
            .layer_gap = 48,
            .pad_x = 16,
            .pad_y = 12},
        "id",
        "requires");
    QVariantList nodes;
    for (const auto& node_value : laid.nodes) {
        QVariantMap node = node_value.toMap();
        node["openable"] = topic_openable(node);
        nodes.push_back(node);
    }
    m_topic_nodes = nodes;
    m_topic_edges = laid.edges;
    m_topic_graph_width = laid.width;
    m_topic_graph_height = laid.height;
}

void Curriculum::set_chapter_by_id(const QString& chapter_id) {
    m_chapter = {};
    m_topics.clear();
    m_chapter_id.clear();
    for (const auto& chapter_value : m_chapters) {
        const QVariantMap chapter = chapter_value.toMap();
        if (chapter.value("id").toString() != chapter_id) {
            continue;
        }
        m_chapter_id = chapter_id;
        m_chapter = chapter;
        for (const auto& topic_value : chapter.value("topics").toList()) {
            m_topics.push_back(topic_value.toMap());
        }
        return;
    }
}

void Curriculum::clear_lab_message() {
    if (m_lab_message.isEmpty()) {
        return;
    }
    m_lab_message.clear();
    emit labMessageChanged();
}
