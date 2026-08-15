#ifndef AUTO_H
#define AUTO_H

#include "product.h"

class AutoA{
public:
    static int get();
};
class AutoB{
public:
    static const char* get();
};

//int add(auto x, auto y) {
//    return x + y;
//}

class Auto : public Product {
public:
    explicit Auto();
    void run() override;

    template <typename T>
    auto get() {
        auto value = T::get();
        //    cout << val << endl;
        //    char str[64] = {0};
        //    snprintf(str, sizeof(str)-1, "%s", val);
        //    return string(str);
        return value;
    }


    template<typename T, typename U>
    auto add(T x, U y) {
        return x + y;
    }

};
REGISTERCLASS(Auto);
#endif // AUTO_H
