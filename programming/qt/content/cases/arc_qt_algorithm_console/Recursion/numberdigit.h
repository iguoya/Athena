#ifndef NUMBERDIGIT_H
#define NUMBERDIGIT_H

#include <task.h>
#include <QStack>
class NumberDigit : public Task
{
    Q_OBJECT
public:
    Q_INVOKABLE explicit NumberDigit();
    void run() override;
    static size_t typeID;


private:
    size_t digit(size_t number);

};

#endif // NUMBERDIGIT_H
