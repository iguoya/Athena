#ifndef BENZCAR_H
#define BENZCAR_H
#include "car.h"

class BenzCar : public Car
{
public:
    BenzCar(Engine& engine) : Car(engine) {};

    void drive() override;
};

#endif // BENZCAR_H
