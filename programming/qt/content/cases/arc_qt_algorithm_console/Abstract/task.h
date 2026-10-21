#ifndef TASK_H
#define TASK_H

#include <QObject>
#include <QVariant>
#include <QStandardItemModel>
//using Vector2D = QVector<QStringList>;


class Task : public QObject
{
    Q_OBJECT
public:
    explicit Task(QObject *parent = nullptr);
    virtual void run() = 0;

    void setNumber(size_t number);
    void setSeries(QVector<int>& series);

    void setParent(QStandardItem* parent);


signals:
    void display(const QString& data);
    void displayList(const QStringList& data);
    void setHeader(const QStringList& data);
    void displayTable(const QVector<QStringList>& data);
    void displayTree();//const QVector<QStringList>& data




protected:

    QString vectorToString(QVector<int>& series);

    size_t m_number;
    QVector<int> m_series;

    QStandardItem* m_parent;

    QStringList series_result;
    QVector<QStringList> table_result;

};


#endif // TASK_H
