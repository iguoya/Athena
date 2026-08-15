#ifndef CONST_H
#define CONST_H

#include "product.h"

class Const : public Product
{
public:
    Const();
    void run() override;
private:
    void const_function() const;
    void const_parameter(const int number);
    int number;
};
REGISTERCLASS(Const);
#endif // CONST_H
