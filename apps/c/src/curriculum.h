#pragma once

#include <QObject>
#include <QUrl>
#include <QVariant>
#include <QVariantList>
#include <QVariantMap>

// 首页是**章**的知识图谱（对齐主程序 C++ 分类图谱）。
// 点章进入该章大纲；大纲里的知识点路线图才能点进教案。
class Curriculum : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString title READ title NOTIFY catalogChanged)
    Q_PROPERTY(QString tagline READ tagline NOTIFY catalogChanged)
    Q_PROPERTY(QVariantList chapters READ chapters NOTIFY catalogChanged)
    Q_PROPERTY(QVariantList graphNodes READ graphNodes NOTIFY catalogChanged)
    Q_PROPERTY(QVariantList graphEdges READ graphEdges NOTIFY catalogChanged)
    Q_PROPERTY(int graphWidth READ graphWidth NOTIFY catalogChanged)
    Q_PROPERTY(int graphHeight READ graphHeight NOTIFY catalogChanged)
    Q_PROPERTY(QVariantMap chapter READ chapter NOTIFY selectionChanged)
    Q_PROPERTY(QVariantList topics READ topics NOTIFY selectionChanged)
    Q_PROPERTY(QVariantList topicNodes READ topicNodes NOTIFY selectionChanged)
    Q_PROPERTY(QVariantList topicEdges READ topicEdges NOTIFY selectionChanged)
    Q_PROPERTY(int topicGraphWidth READ topicGraphWidth NOTIFY selectionChanged)
    Q_PROPERTY(int topicGraphHeight READ topicGraphHeight NOTIFY selectionChanged)
    Q_PROPERTY(int pageIndex READ pageIndex NOTIFY selectionChanged)
    Q_PROPERTY(QString selectedId READ selectedId NOTIFY selectionChanged)
    Q_PROPERTY(QVariantMap selectedTopic READ selectedTopic NOTIFY selectionChanged)
    Q_PROPERTY(QUrl lessonSource READ lessonSource NOTIFY selectionChanged)
    Q_PROPERTY(QString error READ error NOTIFY catalogChanged)
    Q_PROPERTY(QString labMessage READ labMessage NOTIFY labMessageChanged)

public:
    explicit Curriculum(QString root, QObject* parent = nullptr);

    QString title() const { return m_title; }
    QString tagline() const { return m_tagline; }
    QVariantList chapters() const { return m_chapters; }
    QVariantList graphNodes() const { return m_graph_nodes; }
    QVariantList graphEdges() const { return m_graph_edges; }
    int graphWidth() const { return m_graph_width; }
    int graphHeight() const { return m_graph_height; }
    QVariantMap chapter() const { return m_chapter; }
    QVariantList topics() const { return m_topics; }
    QVariantList topicNodes() const { return m_topic_nodes; }
    QVariantList topicEdges() const { return m_topic_edges; }
    int topicGraphWidth() const { return m_topic_graph_width; }
    int topicGraphHeight() const { return m_topic_graph_height; }
    int pageIndex() const;
    QString selectedId() const { return m_selected_id; }
    QVariantMap selectedTopic() const { return m_selected_topic; }
    QUrl lessonSource() const { return m_lesson_source; }
    QString error() const { return m_error; }
    QString labMessage() const { return m_lab_message; }

    Q_INVOKABLE void goHome();
    Q_INVOKABLE void openChapter(const QString& chapter_id);
    Q_INVOKABLE void openOutline();
    Q_INVOKABLE void select(const QString& topic_id);
    Q_INVOKABLE QString difficultyColor(int difficulty) const;
    Q_INVOKABLE QString goalLabel(const QString& goal) const;
    Q_INVOKABLE void launchLab();
    void reload();

signals:
    void catalogChanged();
    void selectionChanged();
    void labMessageChanged();

private:
    enum class Page { Home, Outline, Lesson };

    void rebuild_chapter_graph();
    void rebuild_topic_graph();
    void set_chapter_by_id(const QString& chapter_id);
    void clear_lab_message();

    QString m_root;
    QString m_title;
    QString m_tagline;
    QVariantList m_chapters;
    QVariantList m_graph_nodes;
    QVariantList m_graph_edges;
    int m_graph_width = 800;
    int m_graph_height = 400;
    QVariantMap m_chapter;
    QVariantList m_topics;
    QVariantList m_topic_nodes;
    QVariantList m_topic_edges;
    int m_topic_graph_width = 640;
    int m_topic_graph_height = 200;
    Page m_page = Page::Home;
    QString m_chapter_id;
    QString m_selected_id;
    QVariantMap m_selected_topic;
    QUrl m_lesson_source;
    QString m_error;
    QString m_lab_message;
};
