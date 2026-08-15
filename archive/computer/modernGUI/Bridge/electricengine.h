#ifndef ELECTRICENGINE_H
#define ELECTRICENGINE_H
#include "engine.h"

class ElectricEngine : public Engine
{
public:
    ElectricEngine();
    void start() override;
};

#endif // ELECTRICENGINE_H
