#include "decltype.h"

Decltype::Decltype()
{

}

void Decltype::run()
{
    //    auto m = get_value(1);
    //    display(to_string(m));
    display(format("print_type_info(5) = %d", print_type_info(5)));
    display(format("print_type_info(3.14) = %d", print_type_info(3.14)));
}

decltype(auto) Decltype::get_value(int num)
{
    if(num == 1) {
        return 100;
    }
    return 999;
}
