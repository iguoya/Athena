#pragma once

#include <QObject>
#include <QVariantList>
#include <QVariantMap>

// 内容驱动的路线图目录。它只理解图谱契约，不知道任何具体行业或 QML 组件。
class AtlasCatalog final : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString title READ title NOTIFY catalogChanged)
    Q_PROPERTY(QString subtitle READ subtitle NOTIFY catalogChanged)
    Q_PROPERTY(QVariantList maps READ maps NOTIFY catalogChanged)
    Q_PROPERTY(QString selectedMapId READ selectedMapId NOTIFY selectionChanged)
    Q_PROPERTY(QString selectedMapTitle READ selectedMapTitle NOTIFY selectionChanged)
    Q_PROPERTY(QString selectedMapSummary READ selectedMapSummary NOTIFY selectionChanged)
    Q_PROPERTY(QString selectedMapFamily READ selectedMapFamily NOTIFY selectionChanged)
    Q_PROPERTY(QString selectedCompanionMapId READ selectedCompanionMapId NOTIFY selectionChanged)
    Q_PROPERTY(QString selectedCompanionMapTitle READ selectedCompanionMapTitle NOTIFY selectionChanged)
    Q_PROPERTY(QVariantList nodes READ nodes NOTIFY selectionChanged)
    Q_PROPERTY(QVariantList edges READ edges NOTIFY selectionChanged)
    Q_PROPERTY(int canvasWidth READ canvasWidth NOTIFY selectionChanged)
    Q_PROPERTY(int canvasHeight READ canvasHeight NOTIFY selectionChanged)
    Q_PROPERTY(QVariantMap selectedNode READ selectedNode NOTIFY selectionChanged)
    Q_PROPERTY(QString error READ error NOTIFY catalogChanged)

public:
    explicit AtlasCatalog(QString root, QObject* parent = nullptr);

    QString title() const { return m_title; }
    QString subtitle() const { return m_subtitle; }
    QVariantList maps() const { return m_maps; }
    QString selectedMapId() const { return m_selected_map_id; }
    QString selectedMapTitle() const { return m_selected_map_title; }
    QString selectedMapSummary() const { return m_selected_map_summary; }
    QString selectedMapFamily() const { return m_selected_map_family; }
    QString selectedCompanionMapId() const { return m_selected_companion_map_id; }
    QString selectedCompanionMapTitle() const { return m_selected_companion_map_title; }
    QVariantList nodes() const { return m_nodes; }
    QVariantList edges() const { return m_edges; }
    int canvasWidth() const { return m_canvas_width; }
    int canvasHeight() const { return m_canvas_height; }
    QVariantMap selectedNode() const { return m_selected_node; }
    QString error() const { return m_error; }

    Q_INVOKABLE void openMap(const QString& mapId);
    Q_INVOKABLE void selectNode(const QString& nodeId);
    Q_INVOKABLE void clearSelection();
    Q_INVOKABLE QString relationLabel(const QString& relation) const;
    Q_INVOKABLE QString priorityLabel(const QString& priorityTier) const;
    Q_INVOKABLE QString priorityColor(const QString& priorityTier) const;
    Q_INVOKABLE QString volatilityLabel(const QString& volatility) const;
    Q_INVOKABLE QString validationLabel(const QString& validation) const;
    Q_INVOKABLE QString trackColor(const QString& track) const;
    Q_INVOKABLE QString familyLabel(const QString& family) const;

    bool reload();

signals:
    void catalogChanged();
    void selectionChanged();

private:
    bool loadDocument(QVariantMap* document, QString* error) const;
    bool validateDocument(const QVariantMap& document, QString* error) const;
    void applyMap(const QVariantMap& map);
    void clearMap();

    QString m_root;
    QString m_title;
    QString m_subtitle;
    QVariantList m_maps;
    QString m_selected_map_id;
    QString m_selected_map_title;
    QString m_selected_map_summary;
    QString m_selected_map_family;
    QString m_selected_companion_map_id;
    QString m_selected_companion_map_title;
    QVariantList m_nodes;
    QVariantList m_edges;
    int m_canvas_width = 1280;
    int m_canvas_height = 720;
    QVariantMap m_selected_node;
    QString m_error;
};
