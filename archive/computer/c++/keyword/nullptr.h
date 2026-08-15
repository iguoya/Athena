#ifndef NULLPTR_H
#define NULLPTR_H

#include "product.h"

class Nullptr : public Product
{
public:
    Nullptr();
    void run() override;
private:
    void foo(char *){
        display("when nullptr,  foo(char*)is called");
    }
    void foo(int i) {
        display("when 0 ,  foo(int)is called");
    }
};
REGISTERCLASS(Nullptr);
#endif // NULLPTR_H
