// 第三题：立方增长。线性 / 平方已给，你补三层循环。
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

// TODO(学员)：三层各扫 n，返回步数（约为 n³）。
uint64_t cubic_steps(int n) {
    (void)n;
    return 0; // TODO: 三层循环，最内层 ++steps
}

// —— 以下驱动请勿改 ——
int main() {
    for (int n : {10, 20}) {
        cout << "n=" << n
             << "  linear=" << linear_steps(n)
             << "  quadratic=" << quadratic_steps(n)
             << "  cubic=" << cubic_steps(n)
             << '\n';
    }
    cout << "提示：n 翻倍时 linear≈×2，quadratic≈×4，cubic≈×8。\n";
    return 0;
}
