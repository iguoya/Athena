#include "rabbita.h"

size_t RabbitA::typeID = qRegisterMetaType<RabbitA*>("RabbitA");

RabbitA::RabbitA()
{

}

void RabbitA::run()
{
    size_t sum = 0;
    size_t first = 1;
    size_t second = 1;

    for(size_t i = 1; i < m_number; ++i) {
        sum = first + second;

        QList<QStandardItem*> row;
        QStandardItem *node = new QStandardItem(QString::number(sum));
        row.append(node);
        m_parent->appendRow(row);
        m_parent = node;

        first = second;
        second = sum;
    }

    display("hello world！！");
}
