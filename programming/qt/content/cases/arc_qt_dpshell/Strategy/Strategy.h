#ifndef STRATEGY_H
#define STRATEGY_H
#include <string>
using namespace std;

class Strategy {


public:
    virtual string execute()=0;
};

#endif
