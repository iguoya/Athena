#ifndef HYBRIDENGINE_H
#define HYBRIDENGINE_H

#include "engine.h"
class HybridEngine : public Engine
{
public:
    HybridEngine();
    void start() override;
};

#endif // HYBRIDENGINE_H
