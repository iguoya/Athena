// 第一题：数组堆的下标。父 (i-1)/2，左 2i+1，右 2i+2。
#include <iostream>

using namespace std;

// TODO(学员)：返回下标 i 的父结点下标。i > 0。
int parent_of(int i) {
    (void)i;
    return 0; // TODO: return (i - 1) / 2;
}

// TODO(学员)：返回下标 i 的左孩子下标。
int left_of(int i) {
    (void)i;
    return 0; // TODO: return 2 * i + 1;
}

// —— 以下驱动请勿改 ——
int main() {
    cout << "p5=" << parent_of(5) << '\n';
    cout << "l1=" << left_of(1) << '\n';
    cout << "p2=" << parent_of(2) << '\n';
    return 0;
}
