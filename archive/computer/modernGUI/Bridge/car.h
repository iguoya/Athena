#ifndef CAR_H
#define CAR_H

#include <QObject>
#include "engine.h"

class Car
{
public:
    Car(Engine& engine): engine(engine){};
    virtual void drive() = 0;

protected:
    Engine& engine;
};


#endif // CAR_H
