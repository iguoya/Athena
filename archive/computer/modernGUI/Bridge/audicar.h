#ifndef AUDICAR_H
#define AUDICAR_H
#include "car.h"

class AudiCar : public Car
{
public:
    AudiCar(Engine& engine) : Car(engine) {};

    void drive() override;

};

#endif // AUDICAR_H
