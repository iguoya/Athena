// 三个重载之间，编译器到底选哪个
//
// 值类别决定重载决议，而重载决议决定资源是被复制还是被搬走。让每个重载
// 自己报告一声，规则就不用背了。

#include <iostream>
#include <utility>

using namespace std;

struct Buffer {
    int id;
    explicit Buffer(int value) : id(value) {}
};

// 三个重载覆盖三种绑定能力。
void take(Buffer& b)        { cout << "  → take(Buffer&)        非 const 左值\n"; }
void take(const Buffer& b)  { cout << "  → take(const Buffer&)  谁都能绑，但优先级最低\n"; }
void take(Buffer&& b)       { cout << "  → take(Buffer&&)       右值\n"; }

Buffer make() { return Buffer{99}; }

// —— 示范（已实现，读懂即可）——
void demo_calls() {
    Buffer a{1};
    const Buffer c{2};

    cout << "take(a)              "; take(a);
    cout << "take(c)              "; take(c);
    cout << "take(make())         "; take(make());
    cout << "take(std::move(a))   "; take(std::move(a));
}

// —— 待填 ——
// TODO(学员)：下面这个函数的参数 b 类型是 Buffer&&。
// 在函数体里写一行 take(b); 然后重新编译运行。
//
// 先预测：它会选中三个重载里的哪一个？
//   提示：问自己「表达式 b 的值类别是什么」，而不是「b 的类型是什么」。
//   如果结果和你想的不一样，再试试 take(std::move(b));
void todo_inside_rvalue_parameter(Buffer&& b) {
    cout << "[在 Buffer&& 参数内部] ";
    cout << "（还没写 take 调用）\n";
}

// —— 以下驱动请勿改 ——
int main() {
    demo_calls();
    cout << "---\n";
    todo_inside_rvalue_parameter(Buffer{3});
    return 0;
}
