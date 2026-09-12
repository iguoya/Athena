// 大 O 增长体感：改 n 或循环，重新运行，看步数怎么涨。
#include <cstdint>
#include <iostream>

using namespace std;

uint64_t linear_steps(int n) {
    uint64_t steps = 0;
    for (int i = 0; i < n; ++i) {
        ++steps;
    }
    return steps;
}

uint64_t quadratic_steps(int n) {
    uint64_t steps = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            ++steps;
        }
    }
    return steps;
}

int main() {
    for (int n : {10, 20, 40, 80}) {
        cout << "n=" << n
             << "  linear=" << linear_steps(n)
             << "  quadratic=" << quadratic_steps(n)
             << '\n';
    }
    cout << "提示：n 翻倍时，linear 约翻倍，quadratic 约翻四倍。\n";
    return 0;
}
