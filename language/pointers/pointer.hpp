#pragma once
#include <iostream>

// 指针 —— 指针基础 / 运算 / 数组 / 空指针 / 函数指针
class Pointer {
public:
    void run(std::ostream& os) {
        basic(os);
        arithmetic(os);
        array(os);
        null_ptr(os);
        function_ptr(os);
    }

private:
    // 指针基础：声明、取地址、解引用
    void basic(std::ostream& os) {
        int value = 42;
        int* p = &value;
        os << "value 的地址: " << p << std::endl;
        os << "解引用 *p = " << *p << std::endl;
        *p = 100;
        os << "通过指针修改后 value = " << value << std::endl;
    }

    // 指针运算：ptr++、指针相减
    void arithmetic(std::ostream& os) {
        int arr[] = {10, 20, 30, 40};
        int* p = arr;
        os << "*p = " << *p << std::endl;
        ++p;
        os << "++p 后 *p = " << *p << std::endl;
        os << "指针相减 (p - arr) = " << (p - arr) << std::endl;
    }

    // 指针与数组：数组名是常量指针
    void array(std::ostream& os) {
        int arr[] = {1, 2, 3};
        for (int i = 0; i < 3; ++i) {
            os << "arr[" << i << "] = " << arr[i]
               << "  ==  *(arr+" << i << ") = " << *(arr + i) << std::endl;
        }
    }

    // 空指针与野指针
    void null_ptr(std::ostream& os) {
        int* p = nullptr;
        os << "p 是空指针: " << (p == nullptr ? "是" : "否") << std::endl;

        int* dangling;      // 未初始化的野指针，解引用是未定义行为
        (void)dangling;     // 仅示意，不要解引用
        os << "野指针危险：未初始化的指针不要解引用" << std::endl;
    }

    // 函数指针
    void function_ptr(std::ostream& os) {
        auto add = [](int a, int b) { return a + b; };
        int (*fp)(int, int) = add;   // 无捕获的 lambda 可转为函数指针
        os << "函数指针 fp(3, 4) = " << fp(3, 4) << std::endl;
    }
};

// 源码文本（源码框显示用）
inline const char* POINTER_SOURCE = R"SNIP(class Pointer {
public:
    void run(std::ostream& os) {
        basic(os);
        arithmetic(os);
        array(os);
        null_ptr(os);
        function_ptr(os);
    }

private:
    // 指针基础：声明、取地址、解引用
    void basic(std::ostream& os) { ... }

    // 指针运算：ptr++、指针相减
    void arithmetic(std::ostream& os) { ... }

    // 指针与数组：数组名是常量指针
    void array(std::ostream& os) { ... }

    // 空指针与野指针
    void null_ptr(std::ostream& os) { ... }

    // 函数指针
    void function_ptr(std::ostream& os) { ... }
};)SNIP";
