#include "tuple.h"

Tuple::Tuple()
{

}

tuple<int, double, string> Tuple::multi_return()
{
    return make_tuple(1, 3.14, "中国人");
}

void Tuple::run()
{
    auto [x, y, z] = multi_return();
    display(format("%d , %f, %s ", x, y, z.c_str()));
}
