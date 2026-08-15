#include "nullptr.h"



Nullptr::Nullptr()
{

}

void Nullptr::run()
{
    if(is_same<decltype(NULL), decltype(0)>::value) {
        display("NULL == 0");
    } else {
        display("NULL != 0");
    }

    if(is_same<decltype(NULL), decltype((void*)0)>::value) {
        display("NULL == (void *)0");
    } else {
        display("NULL != (void *)0");
    }



    if(is_same<decltype(NULL), nullptr_t>::value) {
        display("NULL == nullptr");
    } else {
        display("NULL != nullptr");
    }

    foo(0);
//    foo(NULL); //该行不能通过编译
    foo(nullptr);//调用 foo(char*)
}
