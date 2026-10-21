#include "hanoitower.h"

size_t HanoiTower::typeID = qRegisterMetaType<HanoiTower*>("HanoiTower");
HanoiTower::HanoiTower()
{

}

void HanoiTower::run()
{
    setHeader({"当前操作", "起始柱 A", "中转柱 B", "目的柱 C"});
    display("将A柱1-n编号（小到大，从上到下--圆锥型) 圆盘组 借助C柱 放入B柱");
    display("一次只能移动一个圆盘，移动过程要求： 大盘不能压小盘");
    //初始化A柱圆盘

    QStringList originalValue;
    for(size_t i = 1; i <= m_number; ++i) {
        originalValue.push_back(QString::number(i));
    }
    original = {"A", originalValue};
    transmit = {"B", {}};
    destination = {"C", {}};

    operate(original, transmit, destination, m_number);

    displayTable(table_result);

}


void HanoiTower::operate(QPair<QString, QStringList>& from, QPair<QString, QStringList>& middle, QPair<QString, QStringList>& to, size_t n)
{
    if(n == 0) {
        return;
    }
    operate(from, to, middle, n-1);//等价于 将前n-1项 移动到中间节点

    move(from, to);

    operate(middle, from, to, n-1);
}

void HanoiTower::move(QPair<QString, QStringList> &from, QPair<QString, QStringList> &to)
{
    QString number = from.second.front();
    from.second.pop_front();
    to.second.push_front(number);

    QStringList record;
    record<<QString("移动 编号%1圆盘 从 %2 到 %3")
            .arg(number)
            .arg(from.first)
            .arg(to.first);

    record<<original.second.join(" ");
    record<<transmit.second.join(" ");
    record<<destination.second.join(" ");


    table_result.append(record);
}
