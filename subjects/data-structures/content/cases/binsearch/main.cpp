// 第二题：有序数组上二分。先写存在性。
#include <iostream>
#include <vector>

using namespace std;

// TODO(学员)：a 升序。是否存在 x。
bool exists(const vector<int>& a, int x) {
    (void)a;
    (void)x;
    return false; // TODO: 左闭右开，取中点比较
}

// —— 以下驱动请勿改 ——
int main() {
    vector<int> a = {1, 3, 4, 7, 9};
    cout << "has4=" << (exists(a, 4) ? 1 : 0) << '\n';
    cout << "has5=" << (exists(a, 5) ? 1 : 0) << '\n';
    cout << "has1=" << (exists(a, 1) ? 1 : 0) << '\n';
    return 0;
}
