#pragma once
#include <iostream>

// 引用 —— 值传递 vs 引用传递
class Reference {
public:
    void run(std::ostream& os) {
        int x = 5, y = 10;

        swapByValue(x, y);
        os << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << std::endl;

        swapByRef(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << std::endl;
    }

private:
    void swapByValue(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swapByRef(int& a, int& b) {
        int temp = a;
        a = b;
        b = temp;
    }
};

// 源码文本（源码框显示用）
inline const char* REFERENCE_SOURCE = R"SNIP(class Reference {
public:
    void run(std::ostream& os) {
        int x = 5, y = 10;

        swapByValue(x, y);
        os << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << std::endl;

        swapByRef(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << std::endl;
    }

private:
    void swapByValue(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swapByRef(int& a, int& b) {
        int temp = a;
        a = b;
        b = temp;
    }
};)SNIP";
