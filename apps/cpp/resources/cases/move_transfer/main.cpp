// 移动把什么搬走了，源对象之后还剩什么
//
// 每个特殊成员函数报告自己被调用，外加一个「复制了多少个元素」的计数——
// 拷贝和移动的差别在这个数字上一目了然。

#include <iostream>
#include <utility>

using namespace std;

struct Payload {
    static inline long copied_elements = 0;

    size_t size = 0;
    int* data = nullptr;

    explicit Payload(size_t n) : size(n), data(new int[n]{}) {
        cout << "  构造        size=" << size << "\n";
    }
    Payload(const Payload& other) : size(other.size), data(new int[other.size]) {
        for (size_t i = 0; i < size; ++i) { data[i] = other.data[i]; }
        copied_elements += static_cast<long>(size);
        cout << "  拷贝构造    复制了 " << size << " 个元素\n";
    }
    // noexcept 不是装饰：标准库只有确认移动不抛异常时才会用它（C.66）。
    Payload(Payload&& other) noexcept
        : size(other.size), data(other.data) {
        other.data = nullptr;       // 源置空：它的析构不能再释放这块内存
        other.size = 0;
        cout << "  移动构造    接管指针，复制了 0 个元素\n";
    }
    ~Payload() {
        cout << "  析构        size=" << size
             << (data == nullptr ? "（已被移走）" : "") << "\n";
        delete[] data;
    }
};

// —— 示范（已实现，读懂即可）——
void demo_copy() {
    cout << "[拷贝] Payload b = a;\n";
    Payload a{100000};
    Payload b = a;
    cout << "  a 还能用吗：size=" << a.size << "\n";
}

// —— 待填 ——
// TODO(学员)：在下面写一行 `Payload b = std::move(a);`，然后重新编译运行。
//
// 先预测，写完再对照：
//   1. 会调用拷贝构造还是移动构造？
//   2. 末尾统计的「累计复制元素数」会增加多少？
//   3. 这一行之后 a.size 是多少？a 还能安全析构吗？
void todo_move() {
    cout << "[移动] Payload b = std::move(a);\n";
    Payload a{100000};

    cout << "  （还没写，所以 a 原封不动）  a.size=" << a.size << "\n";
}

// —— 以下驱动请勿改 ——
int main() {
    demo_copy();
    cout << "---\n";
    todo_move();
    cout << "---\n";
    cout << "累计复制元素数：" << Payload::copied_elements << "\n";
    return 0;
}
