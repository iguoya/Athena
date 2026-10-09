// 第一题：爬楼梯。dp[i] = dp[i-1] + dp[i-2]。
#include <iostream>
#include <vector>

using namespace std;

// TODO(学员)：n 阶楼梯，每次 1 或 2 阶，有多少种走法。n >= 1。
int ways(int n) {
    (void)n;
    return 0; // TODO: 边界 1、2，再递推
}

// —— 以下驱动请勿改 ——
int main() {
    cout << "w1=" << ways(1) << '\n';
    cout << "w3=" << ways(3) << '\n';
    cout << "w4=" << ways(4) << '\n';
    return 0;
}
