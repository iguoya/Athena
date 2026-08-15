#ifndef DECLTYPE_H
#define DECLTYPE_H

#include "product.h"
class Decltype : public Product
{
public:
    Decltype();
    void run() override;

    template<typename T>
    auto print_type_info(const T& t){
        if constexpr(is_integral<T>::value){
            return t + 1;
        } else {
            return t +0.0015926;
        }
    }


    decltype (auto) get_value(int num);
};
REGISTERCLASS(Decltype);
#endif // DECLTYPE_H
