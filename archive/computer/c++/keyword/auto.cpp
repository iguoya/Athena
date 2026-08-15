#include "auto.h"



Auto::Auto() {}

void Auto::run() {
    display(format("类型A : get 返回 %d",  get<AutoA>()));
    display(format("类型B : get 返回 %s",  get<AutoB>()));

    auto x = 1;
    auto y = 3.14;
    decltype(x+y) z;

    if(is_same<decltype(x), int>::value)
        display("type x == int");
    if(is_same<decltype(y), float>::value)
        display("type y == float");
    if(is_same<decltype(y), double>::value)
        display("type y == double");

    if(is_same<decltype(y), decltype(z)>::value)
        display("type z == type x");

    auto result = add<int, double>(100, 9.18);
    display(format("result = %d", result));
    //    display(get<AutoB>());
}



const char *AutoB::get()
{
    return "http://c.biancheng.net/cplus/";
}

int AutoA::get()
{
    return 100;
}
