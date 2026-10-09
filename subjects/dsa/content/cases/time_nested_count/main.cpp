// 第二题：内层次数跟外层有关。方阵和折半已给，你补三角。
#include <cstdint>
#include <iostream>

using namespace std;

uint64_t demo_square(int n) {
    uint64_t steps = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            ++steps;
        }
    }
    return steps;
}

uint64_t variant_halving(int n) {
    uint64_t steps = 0;
    for (int x = n; x > 0; x /= 2) {
        ++steps;
    }
    return steps;
}

// TODO(学员)：外层 i=0..n-1，内层 j=0..i，返回步数（应为 n(n+1)/2）。
uint64_t todo_triangle(int n) {
    (void)n;
    return 0; // TODO: 内层到 i 为止
}

// —— 以下驱动请勿改 ——
int main() {
    for (int n : {8, 16}) {
        cout << "n=" << n
             << "  square=" << demo_square(n)
             << "  triangle=" << todo_triangle(n)
             << "  halving=" << variant_halving(n)
             << '\n';
    }
    cout << "提示：triangle 应为 1+…+n = n(n+1)/2；主导仍是平方。\n";
    return 0;
}
