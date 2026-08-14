#pragma once
#include <iostream>

// 引用 —— 引用基础 / const 引用 / 值传递 vs 引用传递 / 引用返回值
class Reference {
public:
    void run(std::ostream& os) {
        basic(os);
        const_ref(os);
        pass_by(os);
        return_ref(os);
    }

public:
    // 引用基础：别名、必须初始化、不能重新绑定
    void basic(std::ostream& os) {
        int x = 10;
        int& ref = x;          // ref 是 x 的别名
        ref = 20;
        os << "x = " << x << " (引用修改了原值)" << std::endl;
        os << "&ref == &x: " << (&ref == &x ? "是" : "否") << std::endl;
    }

    // const 引用：可绑定临时对象、延长生命周期
    void const_ref(std::ostream& os) {
        const int& r = 42;     // const 引用可绑定右值/临时对象
        os << "const 引用绑定字面量: r = " << r << std::endl;

        std::string s = "hello";
        const std::string& cs = s;
        os << "const 引用长度: " << cs.size() << std::endl;
    }

    // 值传递 vs 引用传递
    void pass_by(std::ostream& os) {
        int x = 5, y = 10;

        swapByValue(x, y);
        os << "值传递后:   x=" << x << ", y=" << y << "  (未改变)" << std::endl;

        swapByRef(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << std::endl;
    }

    // 引用作为返回值
    void return_ref(std::ostream& os) {
        int arr[] = {100, 200, 300};

        int& r = element(arr, 1);   // 返回引用，可直接赋值
        r = 999;
        os << "通过引用返回值修改后 arr[1] = " << arr[1] << std::endl;
    }

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

    static int& element(int* arr, int i) {
        return arr[i];
    }
};

