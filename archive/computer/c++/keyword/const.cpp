#include "const.h"

Const::Const() : number(1000)
{

}

void Const::run()
{
    /* const  用法灵活, 大大改善程序的健壮性 */
    const int a = 1;
    display(format("情况1 : const a = %d",  a));
    //a = 2; !!!!!!
    //情况2 : 类型检查
    const_function();
    const_parameter(666);

    const char *p1 = "China";
    char p2[] = "Japan";
    // *p1 = "Japan"; !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    display(format("情况4 : const char *p1 = China, *p1 = %s",  p1));
    p1 = p2;
    display(format("情况5 : *p1 = %s", p1));

    int *const p3 = &number;
//    const int i = 1000;
//    p3 = &i;
    display(format("情况5 : before int *const p3 = %d", p3));
    number = 99999;
    display(format("after number = 99999, int *const p3 = %d", p3));
}

void Const::const_function() const
{
    //    number += 200;
    display(format("情况2：常成员函数 %d",  number));
}

void Const::const_parameter(const int number)
{
    //    num = 10000;
    display(format("情况3：const参数 %d",  number));
}


