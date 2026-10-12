// 加一个析构函数，移动就悄悄没了
//
// Core Guidelines C.21：声明任何一个拷贝 / 移动 / 析构函数——哪怕写成
// =default 或 =delete——都会抑制移动构造与移动赋值的隐式声明。
// 这个抑制不报错、不警告，只能靠观察调用了哪个构造函数才发现。

#include <iostream>
#include <utility>
#include <vector>

using namespace std;

// —— 示范：什么都不声明，六个特殊成员函数编译器全包 ——
struct Clean {
    vector<int> payload;

    explicit Clean(size_t n) : payload(n, 0) {}
    // 没有析构、没有拷贝、没有移动——移动操作会被隐式生成。
};

// —— 示范：只多了一个析构函数 ——
struct WithDtor {
    vector<int> payload;

    explicit WithDtor(size_t n) : payload(n, 0) {}
    ~WithDtor() {}      // 只是一个空析构，什么也没做
    // 按 C.21，移动构造与移动赋值从此不再隐式生成。
};

// 编译期就能问出答案：这个类型从右值构造时，走的是移动还是拷贝。
template <typename T>
void report(const char* name) {
    cout << "  " << name
         << "  可移动构造=" << is_move_constructible_v<T>
         << "  而实际从右值构造时是否走移动="
         << (is_nothrow_move_constructible_v<T> ? "是" : "否（退回拷贝）")
         << "\n";
}

void demo_suppression() {
    cout << "[两个类的差别只有一个空析构函数]\n";
    report<Clean>("Clean   ");
    report<WithDtor>("WithDtor");
    cout << "  注意 is_move_constructible 两个都是 1——因为拷贝构造也能接住右值。\n";
    cout << "  真正的差别在第二列：WithDtor 的「移动」实际是拷贝。\n";
}

// —— 待填 ——
// TODO(学员)：给 WithDtor 补回移动操作，让它重新走移动。
// 在 WithDtor 里加这两行：
//     WithDtor(WithDtor&&) noexcept = default;
//     WithDtor& operator=(WithDtor&&) noexcept = default;
//
// 先预测：
//   1. 补上之后 report<WithDtor> 的第二列会变成什么？
//   2. 为什么 =default 就够了，不用自己写实现？
//   3. 按 C.21，补了移动操作之后，拷贝操作会怎样？（这一条容易忽略）

// —— 以下驱动请勿改 ——
int main() {
    demo_suppression();
    return 0;
}
