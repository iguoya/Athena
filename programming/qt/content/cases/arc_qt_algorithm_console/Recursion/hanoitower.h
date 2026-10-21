#ifndef HANOITOWER_H
#define HANOITOWER_H

#include <task.h>
#include <QStringList>
#include <QPair>

class HanoiTower : public Task
{
    Q_OBJECT
public:
    Q_INVOKABLE HanoiTower();
    static size_t typeID;
    void run() override;
private:
    void operate(QPair<QString, QStringList>& from, QPair<QString, QStringList>& middle, QPair<QString, QStringList>& to, size_t n);
    void move(QPair<QString, QStringList>& from, QPair<QString, QStringList>& to);

    QPair<QString, QStringList> original;
    QPair<QString, QStringList> transmit;
    QPair<QString, QStringList> destination;


};

#endif // HANOITOWER_H
