// 技能练习：给循环「数步」——改代码前先预测，再对照输出。
#include <cstdint>
#include <iostream>

using namespace std;

// 示范：两层循环，内层与 i 无关时，步数是 n * n。
uint64_t demo_square(int n) {
    uint64_t steps = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            ++steps; // 计一次「基本操作」
        }
    }
    return steps;
}

// 变式 A：内层跑到 i（含），步数约为 n(n+1)/2 → Θ(n²) 仍成立。
uint64_t variant_triangle(int n) {
    uint64_t steps = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j <= i; ++j) {
            ++steps;
        }
    }
    return steps;
}

// 变式 B：每次把区间砍半 —— Θ(log n)
uint64_t variant_halving(int n) {
    uint64_t steps = 0;
    for (int x = n; x > 0; x /= 2) {
        ++steps;
    }
    return steps;
}

int main() {
    for (int n : {8, 16, 32}) {
        cout << "n=" << n
             << "  square=" << demo_square(n)
             << "  triangle=" << variant_triangle(n)
             << "  halving=" << variant_halving(n)
             << '\n';
    }
    cout << "练习：再加一个「三层各扫 n」的函数，预测步数后实现并验证。\n";
    return 0;
}
