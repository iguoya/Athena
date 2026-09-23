// 初始化形式：差别藏在「调用了哪个构造函数」里
//
// 同样带一个等号，Tracer copy = a; 和 Tracer b = 2; 走的不是一条路。
// 想弄清楚，最直接的办法是让每个特殊成员函数自己报告一声。

#include <iostream>
#include <utility>

using namespace std;

struct Tracer {
    int id;

    // 非 explicit：允许从 int 隐式转换过来，下面的拷贝初始化才有戏看。
    Tracer(int value) : id(value) {
        cout << "  转换构造 Tracer(int)  id=" << id << "\n";
    }
    Tracer(const Tracer& other) : id(other.id) {
        cout << "  拷贝构造          id=" << id << "\n";
    }
    Tracer(Tracer&& other) noexcept : id(std::exchange(other.id, -1)) {
        cout << "  移动构造          id=" << id << "\n";
    }
    ~Tracer() {
        cout << "  析构              id=" << id << "\n";
    }
};

// —— 示范（已实现，读懂即可）——
// 两行都只是「创建一个对象」，但构造函数的调用完全不同。
void demo_direct_init() {
    cout << "[直接初始化] Tracer a{1};\n";
    Tracer a{1};

    cout << "[从已有对象拷贝] Tracer copy = a;\n";
    Tracer copy = a;

    cout << "(离开作用域，按构造的逆序析构)\n";
}

// —— 待填 ——
// TODO(学员)：在下面写一行 `Tracer b = 2;`，然后重新编译运行。
//
// 写之前先预测，把答案记在心里再跑：
//   1. 这一行会打印几次构造？
//   2. 会不会先用 2 建一个临时 Tracer，再把它拷贝（或移动）给 b？
//   3. 它和示范里的 `Tracer copy = a;` 都带等号，打印出来会一样吗？
//
// 跑完对照结果——如果和你的预测不同，那个差异就是这个实验的全部价值。
void todo_copy_init() {
    cout << "[拷贝初始化] Tracer b = 2;\n";

    cout << "(还没写，所以上面什么都没发生)\n";
}

// —— 以下驱动请勿改 ——
int main() {
    demo_direct_init();
    cout << "---\n";
    todo_copy_init();
    return 0;
}
