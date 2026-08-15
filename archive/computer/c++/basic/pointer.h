#ifndef POINTER_H
#define POINTER_H

#include "product.h"

class Pointer : public Product
{
public:
    Pointer();
    void run() override;
};
REGISTERCLASS(Pointer);
#endif // POINTER_H
