#ifndef RABBITA_H
#define RABBITA_H

#include "task.h"


class RabbitA : public Task
{
    Q_OBJECT
public:
    static size_t typeID;
    Q_INVOKABLE RabbitA();
    void run() override;

private:

};

//Q_DECLARE_METATYPE(RabbitA*)

#endif // RABBITA_H
