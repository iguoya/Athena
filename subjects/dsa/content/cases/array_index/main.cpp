// 第一题：按下标取值。连续布局的超能力就是 a[i]。
#include <iostream>
#include <vector>

using namespace std;

// TODO(学员)：返回 a 的第 i 个元素（下标从 0 起）。
int at(const vector<int>& a, size_t i) {
    (void)a;
    (void)i;
    return 0; // TODO: return a[i];
}

// —— 以下驱动请勿改 ——
int main() {
    vector<int> a = {10, 20, 30, 40, 50};
    cout << "at0=" << at(a, 0) << '\n';
    cout << "at3=" << at(a, 3) << '\n';
    return 0;
}
