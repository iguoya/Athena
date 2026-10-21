#include "task.h"

Task::Task(QObject *parent) : QObject(parent)
{

}

QString Task::vectorToString(QVector<int> &series)
{
    QString result;
    for(auto m : series) {
        result.append(QString::number(m)+" ");
    }
    return result;
}


void Task::setNumber(size_t number)
{
    m_number = number;
}

void Task::setSeries(QVector<int> &series)
{
    m_series = series;
}

void Task::setParent(QStandardItem *parent)
{
    m_parent = parent;
}

