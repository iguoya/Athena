// 第一题：只数一层循环。骨架能编译；你补全 todo_count。
#include <cstdint>
#include <iostream>

using namespace std;

// —— 参考：扫 n 次 ——
uint64_t demo_count(int n) {
    uint64_t steps = 0;
    for (int i = 0; i < n; ++i) {
        ++steps;
    }
    return steps;
}

// TODO(学员)：照着上面写一遍，返回「基本操作」次数（应等于 n）。
uint64_t todo_count(int n) {
    (void)n;
    return 0; // TODO: 循环 n 次，每次 ++steps
}

// —— 以下驱动请勿改 ——
int main() {
    cout << "demo=" << demo_count(5) << '\n';
    cout << "count=" << todo_count(5) << '\n';
    cout << "count=" << todo_count(8) << '\n';
    return 0;
}
