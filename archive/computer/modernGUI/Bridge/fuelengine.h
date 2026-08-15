#ifndef FUELENGINE_H
#define FUELENGINE_H

#include "engine.h"
class FuelEngine : public Engine
{
public:
    FuelEngine();
    void start() override;
};

#endif // FUELENGINE_H
