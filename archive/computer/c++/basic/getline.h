#ifndef GETLINE_H
#define GETLINE_H

#include "product.h"

class Getline : public Product
{
public:
    Getline();
    void run() override;
};
REGISTERCLASS(Getline);
#endif // GETLINE_H
