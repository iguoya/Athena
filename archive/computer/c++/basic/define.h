#ifndef DEFINE_H
#define DEFINE_H

#include "product.h"
class Define : public Product
{
public:
    Define();
    void run() override;
};
REGISTERCLASS(Define);
#endif // DEFINE_H
