#include "rabbit.h"

size_t Rabbit::typeID = qRegisterMetaType<Rabbit*>("Rabbit");

Rabbit::Rabbit()
{

}

void Rabbit::run()
{
    setHeader({"树形结构", "第一个数", "第二个数", "结果"});

    fibonacci(m_number);
    //    for(size_t i = 1; i < m_number; ++i) {
    //        series_result<<QString::number(fibonacci(i));
    //    }




}

size_t Rabbit::fibonacci(size_t number)
{
    if(number <= 2) {
        return 1;
    }
//    auto result = fibonacci(number-1) + fibonacci(number-2);
    auto first = fibonacci(number-2);
    auto second = fibonacci(number-1);
    auto result = first + second;

    QList<QStandardItem*> row;

    QStandardItem *nodeD = new QStandardItem(QString::number(number));
    row.append(nodeD);

    QStandardItem *nodeA = new QStandardItem(QString::number(first));
    row.append(nodeA);
    QStandardItem *nodeB = new QStandardItem(QString::number(second));
    row.append(nodeB);
    QStandardItem *nodeC = new QStandardItem(QString::number(result));
    row.append(nodeC);

    m_parent->appendRow(row);
    m_parent = nodeD;

    return result;
}
