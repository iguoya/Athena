#pragma once
#include <iostream>

using namespace std;

// 引用 —— 引用基础 / const 引用 / 值传递 vs 引用传递 / 引用返回值
class Reference {
public:
    void run(ostream& os) {
        reference_basics(os);
        const_reference(os);
        pass_by_reference(os);
        return_by_reference(os);
    }

public:
    // 引用基础：别名、必须初始化、不能重新绑定
    void reference_basics(ostream& os) {
        int x = 10;
        int& ref = x;          // ref 是 x 的别名
        ref = 20;
        os << "x = " << x << " (引用修改了原值)" << endl;
        os << "&ref == &x: " << (&ref == &x ? "是" : "否") << endl;

        int y = 30;
        ref = y; // 不能重新绑定引用，ref 仍然是 x
        int &z = y; // 正确：z 是 y 的别名
        os << "ref = " << ref << ", z = " << z << endl;
    }

    // const 引用：可绑定临时对象、延长生命周期
    void const_reference(ostream& os) {
        const int& r = 42;     // const 引用可绑定右值/临时对象
        os << "const 引用绑定字面量: r = " << r << endl;

        string s = "hello";
        const string& cs = s;
        os << "const 引用长度: " << cs.size() << endl;
    }

    // 值传递 vs 引用传递
    void pass_by_reference(ostream& os) {
        int x = 5, y = 10;

        swap_by_value(x, y);
        os << "值传递后:   x=" << x << ", y=" << y << "  (未改变)" << endl;

        swap_by_reference(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << endl;

        int m = 100, n = 200;
        swap_by_reference(m, n);
        os << "引用传递后: m=" << m << ", n=" << n << "  (已交换)" << endl;
    }

    // 引用作为返回值
    void return_by_reference(ostream& os) {
        int arr[] = {100, 200, 300};

        int& r = element(arr, 1);   // 返回引用，可直接赋值
        r = 999;
        os << "通过引用返回值修改后 arr[1] = " << arr[1] << endl;
    }

    void swap_by_value(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swap_by_reference(int& a, int& b) {
        int temp = a;
        a = b;
        b = temp;
    }

    static int& element(int* arr, int i) {
        return arr[i];
    }
};
