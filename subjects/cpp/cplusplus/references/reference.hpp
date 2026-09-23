#pragma once
#include <iostream>

using namespace std;

// 匿名命名空间里的辅助类型只服务本文件的知识点演示；每个包含本文件的
// 翻译单元各自拿到一份内部链接的副本，不会跨翻译单元冲突。
namespace {

// const_reference()：靠析构计数观察临时对象什么时候真正被销毁，
// 而不是靠猜测——"生命周期延长"必须能看见效果才算讲清楚。
class TrackedString {
public:
    TrackedString(string value, int& destruction_count)
        : m_value(std::move(value)), m_destruction_count(destruction_count) {}
    ~TrackedString() { ++m_destruction_count; }

    const string& value() const { return m_value; }

private:
    string m_value;
    int& m_destruction_count;
};

// 把一个已经是引用的形参原样转发返回——绑定到它的临时对象并不会因此
// 被延长生命周期，因为这里没有发生"引用直接绑定到一个纯右值"的动作。
// 不叫 identity：std::identity 是 <functional> 里 C++20 新增的类型，
// 跟 using namespace std 撞名会产生二义性。
const TrackedString& pass_through(const TrackedString& value) { return value; }

// pass_by_reference()：用拷贝计数把"复制成本"从概念变成能读出来的数字。
class CopyCounter {
public:
    explicit CopyCounter(int& copy_count) : m_copy_count(&copy_count) {}
    CopyCounter(const CopyCounter& other) : m_copy_count(other.m_copy_count) {
        ++*m_copy_count;
    }

private:
    int* m_copy_count;
};

void take_by_value(CopyCounter value) { (void)value; }
void take_by_reference(const CopyCounter& value) { (void)value; }

// return_by_reference()：安全示范"返回成员引用"，对照组里保留危险写法
// 的源码但不编译、不执行——返回局部变量的引用是未定义行为，实际运行
// 这段代码本身就不是一个定义良好的演示。
class Counter {
public:
    int& value() { return m_value; }

private:
    int m_value = 0;
};

// int& dangling_reference() {
//     int local = 123;
//     return local; // 主流编译器通常能警告，如 GCC/Clang 的 -Wreturn-stack-address
// }
//
// int& dangling_through_pointer() {
//     int local = 123;
//     int* pointer = &local;
//     return *pointer; // 经过一层指针转发，很多编译器的警告不再能可靠识别
// }

} // namespace

// 引用 —— 引用基础 / const 引用 / 值传递 vs 引用传递 / 引用返回值
class Reference {
public:
    // 引用基础：别名、必须初始化、不能重新绑定
    void reference_basics(ostream& os) {
        int x = 10;
        int& ref = x;          // ref 是 x 的别名
        ref = 20;
        os << "x = " << x << " (引用修改了原值)" << endl;
        os << "&ref == &x: " << (&ref == &x ? "是" : "否") << endl;

        // int& invalid; // 编译错误：引用必须在声明时初始化，不能先声明后绑定
        os << "引用必须在声明时初始化，不能像指针那样先声明再赋值" << endl;

        int y = 30;
        ref = y; // 不能重新绑定引用，这是赋值，ref 仍然是 x 的别名
        int &z = y; // 正确：z 是 y 的别名
        os << "ref = " << ref << " (仍是 x 的别名，被赋成了 y 的值), z = " << z << endl;
    }

    // const 引用：只读语义、延长临时对象生命周期、该规则的作用域边界
    void const_reference(ostream& os) {
        const int& r = 42;     // const 引用可绑定右值/临时对象
        os << "const 引用绑定字面量: r = " << r << endl;

        int destroyed_in_scope = 0;
        {
            const TrackedString& extended = TrackedString("临时对象", destroyed_in_scope);
            os << "const 引用绑定临时对象后仍可正常访问: " << extended.value() << endl;
            os << "作用域内临时对象尚未析构，析构次数: " << destroyed_in_scope << endl;
        }
        os << "const 引用离开作用域后，临时对象才跟着析构，析构次数: "
           << destroyed_in_scope << endl;

        int destroyed_via_function = 0;
        {
            const TrackedString& via_function =
                pass_through(TrackedString("经函数转发", destroyed_via_function));
            (void)via_function; // 生命周期延长规则在这里不适用，不安全读取它
            os << "临时对象经函数参数转发后，语句结束时已经析构，析构次数: "
               << destroyed_via_function << endl;
        }
        os << "延长生命周期只在引用直接绑定纯右值的那一条语句里生效，"
              "经过一层函数转发就不再适用" << endl;
    }

    // 值传递 vs 引用传递：可修改性 + 复制成本
    void pass_by_reference(ostream& os) {
        int x = 5, y = 10;

        swap_by_value(x, y);
        os << "值传递后:   x=" << x << ", y=" << y << "  (未改变)" << endl;

        swap_by_reference(x, y);
        os << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << endl;

        int copy_count = 0;
        CopyCounter counter(copy_count);
        take_by_value(counter);
        os << "值传递触发一次拷贝构造，拷贝次数: " << copy_count << endl;
        take_by_reference(counter);
        os << "引用传递不需要拷贝，次数仍为: " << copy_count << endl;
    }

    // 引用作为返回值：安全用法（成员/生命周期更长的对象），以及为什么
    // 返回局部变量引用是未定义行为
    void return_by_reference(ostream& os) {
        int arr[] = {100, 200, 300};

        int& r = element(arr, 1);   // 返回引用，可直接赋值
        r = 999;
        os << "返回数组元素引用可安全修改原数组: arr[1] = " << arr[1] << endl;

        Counter counter;
        int& member_ref = counter.value();
        member_ref = 7;
        os << "返回成员引用，只要对象自己还活着就安全: " << counter.value() << endl;

        os << "返回局部变量的引用是未定义行为：函数返回后栈帧被回收，"
              "引用指向的内存随时可能被覆盖" << endl;
        os << "直接返回局部变量名，主流编译器通常能给出警告"
              "（如 GCC/Clang 的 -Wreturn-stack-address）" << endl;
        os << "但经过一层指针或另一个函数转发后再返回，警告经常失效，"
              "这正是这类 bug 危险、容易漏查的地方" << endl;
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
