#ifndef TUPLE_H
#define TUPLE_H
#include "product.h"

class Tuple : public Product
{
public:
    Tuple();
    void run() override;

    tuple<int, double, string> multi_return();
};
REGISTERCLASS(Tuple);
#endif // TUPLE_H
