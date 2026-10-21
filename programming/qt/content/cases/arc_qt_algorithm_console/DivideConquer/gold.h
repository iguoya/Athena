#ifndef GOLD_H
#define GOLD_H

#include <task.h>

class Gold : public Task
{
    Q_OBJECT
public:
    Q_INVOKABLE Gold();

    void run() override;
private:
    static size_t typeID;
};

#endif // GOLD_H
