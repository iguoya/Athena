#include "pointer.h"

Pointer::Pointer()
{

}

void Pointer::run()
{

    int arr[] = {10, 100, 200, 222, 3, 3, 5};
    int *ptr;

    // 指针中的数组地址
    ptr = arr;
    for (size_t i = 0; i < sizeof(arr)/sizeof(int); i++)
    {
        display(format("地址: %p, 值: %d", ptr, *ptr));
        // 移动到下一个位置
        ptr++;
    }

    const char *chapters[] = {
        "异常处理",
        "动态内存",
        "信号处理",
        "多线程",
        "Web编程",
        "数据抽象",
        "数据封装"
    };

    for (size_t i = 0; i < 7; ++i)
    {
        display(format("第 %d 章:\t\t %s", i, chapters[i]));
    }


}
