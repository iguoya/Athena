#pragma once

#include <functional>
#include <ostream>
#include <string>
#include <vector>

using namespace std;

// 匿名命名空间里的辅助类型和函数只服务本文件的知识点演示；每个包含
// 本文件的翻译单元各自拿到一份内部链接的副本，不会跨翻译单元冲突。
namespace {

// overload()：同名函数按参数类型和个数区分，重载解析在编译期完成，
// 运行时没有分支判断；第三个重载额外带一个默认参数。
int describe(int value) { return value * 2; }
double describe(double value) { return value * 2.0; }
string describe(const string& value, int repeat = 1) {
    string result;
    for (int i = 0; i < repeat; ++i) {
        result += value;
    }
    return result;
}

// function_object()：重载了 operator() 的类类型对象——跟普通函数不同，
// 它能在对象内部携带状态，调用之间自动累积，不需要外部变量配合。
class Accumulator {
public:
    int operator()(int delta) {
        m_total += delta;
        return m_total;
    }
    int total() const { return m_total; }

private:
    int m_total = 0;
};

// 对照组：普通函数没有自己的存储，状态只能靠调用方在外部维护、每次
// 显式传进来再传出去。
int add_without_state(int total, int delta) { return total + delta; }

// 对照组：函数指针调用要经过一层间接跳转，编译器一般不会跨这层内联；
// 函数对象的调用运算符类型在编译期就固定，更容易被展开进调用点。
int square(int value) { return value * value; }
int call_with(int value, int (*operation)(int)) { return operation(value); }

// function_wrapper()：std::function 能统一存放函数指针、函数对象和
// Lambda——这里提供其中两种来源，Lambda 直接在方法体里现场写。
int double_value(int value) { return value * 2; }
struct Doubler {
    int operator()(int value) const { return value * 2; }
};

} // namespace

// 函数与可调用对象
//
// 一个 public 成员函数对应 athena.json 中的一个可运行知识点。
class FunctionCallable {
public:
    void overload(ostream& output) const {
        output << "describe(int): " << describe(4) << '\n';
        output << "describe(double): " << describe(4.5) << '\n';
        output << "describe(string, 默认 repeat=1): " << describe(string("ab")) << '\n';
        output << "describe(string, repeat=3): " << describe(string("ab"), 3) << '\n';
        output << "重载解析依据实参类型和数量在编译期选定版本，"
                  "不是运行时按条件分支\n";
    }

    void function_object(ostream& output) const {
        Accumulator accumulator;
        output << "函数对象自带状态，调用间自动累加: " << accumulator(3) << '\n';
        output << "再调用一次继续累加: " << accumulator(4) << '\n';
        output << "累加器当前总和: " << accumulator.total() << '\n';

        int total = 0;
        total = add_without_state(total, 3);
        total = add_without_state(total, 4);
        output << "普通函数没有自身存储，状态只能靠外部变量维护: " << total << '\n';

        output << "call_with(6, square) 经函数指针间接调用: " << call_with(6, square)
               << '\n';
        output << "函数对象的调用运算符类型在编译期固定，比函数指针更容易被内联，"
                  "标准算法（如 std::sort 的比较器）和 Lambda 都以它为底层机制\n";
    }

    void lambda(ostream& output) const {
        int base = 10;
        auto by_value = [base](int x) { return base + x; };
        auto by_reference = [&base](int x) { return base + x; };
        output << "按值捕获复制快照，base=" << base << " 时 by_value(5)=" << by_value(5)
               << '\n';

        base = 100;
        output << "原 base 改为 100 后，by_value(5) 仍用旧快照: " << by_value(5) << '\n';
        output << "by_reference(5) 跟着看到新值: " << by_reference(5) << '\n';

        auto counter = [count = 0]() mutable { return ++count; };
        output << "mutable 允许修改按值捕获的副本，第一次调用: " << counter() << '\n';
        output << "第二次调用: " << counter() << '\n';
        output << "第三次调用: " << counter() << '\n';

        auto deduced = [](int x, int y) { return x + y; }; // 返回类型由 auto 自动推导
        output << "返回类型自动推导，deduced(2, 3) = " << deduced(2, 3) << '\n';

        output << "隐式捕获 [&] 或 [=] 会自动捕获用到的每个外部变量，写法简洁，"
                  "但容易在不经意间捕获了不该共享的变量\n";
        // 危险模式：按引用捕获局部变量，Lambda 却被带出这个局部变量的作用域，
        // 只保留代码说明问题、不实际执行——调用它会读取已经销毁的栈内存，是
        // 未定义行为。
        // auto make_dangling = []() {
        //     int local = 1;
        //     return [&local]() { return local; }; // 捕获的是即将销毁的 local
        // };
        // auto dangling = make_dangling(); // local 已随 make_dangling() 返回而销毁
        // dangling(); // 未定义行为，这里不会执行
        output << "按引用捕获局部变量、并在其生命周期结束后调用是未定义行为，"
                  "最常见于把 Lambda 从函数里返回出去、或存进容器留到后面再调用\n";
    }

    void function_wrapper(ostream& output) const {
        vector<function<int(int)>> callables;
        callables.push_back(double_value);              // 函数指针
        callables.push_back(Doubler{});                  // 函数对象
        callables.push_back([](int value) { return value + 1; }); // Lambda

        for (size_t i = 0; i < callables.size(); ++i) {
            output << "callables[" << i << "](5) = " << callables[i](5) << '\n';
        }
        output << "std::function 用类型擦除统一存放函数指针、函数对象和 Lambda，"
                  "每次调用都经过一层间接转发，比直接调用多一点开销\n";

        function<int(int)> empty;
        try {
            empty(1);
        } catch (const bad_function_call& error) {
            output << "调用空 std::function 抛出 bad_function_call: " << error.what()
                   << '\n';
        }
    }

    void callback(ostream& output) const {
        int notified_value = 0;
        function<void(int)> on_change = [&notified_value](int value) {
            notified_value = value;
        };

        auto trigger = [](int value, const function<void(int)>& handler) {
            handler(value);
        };
        trigger(42, on_change);
        output << "回调按引用捕获了调用方的局部变量，触发后同步写入: "
               << notified_value << '\n';

        output << "这次调用之所以安全，是因为 notified_value 在触发回调时依旧存活；"
                  "如果把 on_change 保存起来，留到 notified_value 所在函数返回之后\n"
                  "才触发，就会经悬空引用写入已经销毁的内存\n";
        output << "更安全的做法：回调按值捕获需要的数据，或者持有 shared_ptr 明确\n"
                  "共享所有权，不要假设回调一定会在提供方对象存活期间被调用\n";
    }
};
