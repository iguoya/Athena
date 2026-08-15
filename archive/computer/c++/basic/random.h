#ifndef RANDOM_H
#define RANDOM_H

#include "product.h"
#include <random>
#include <functional>

class Random : public Product
{
public:
    Random();
    void run() override;
};
REGISTERCLASS(Random);
#endif // RANDOM_H
