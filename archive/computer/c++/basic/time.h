#ifndef TIME_H
#define TIME_H

#include "product.h"

class Time : public Product
{
public:
    Time();
    void run() override;
};
REGISTERCLASS(Time);
#endif // TIME_H
