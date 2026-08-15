#ifndef BMWCAR_H
#define BMWCAR_H
#include "car.h"

class BMWCar : public Car
{
public:

    BMWCar(Engine& engine) : Car(engine) {};

    void drive() override;
};

#endif // BMWCAR_H
