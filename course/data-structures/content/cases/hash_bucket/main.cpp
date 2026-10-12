// 第一题：键落到几号桶。哈希的第一步就是 key % m。
#include <iostream>

using namespace std;

// TODO(学员)：返回 key 映射到 [0, m) 的桶号。m > 0。
int bucket(int key, int m) {
    (void)key;
    (void)m;
    return 0; // TODO: return key % m;
}

// —— 以下驱动请勿改 ——
int main() {
    cout << "b7=" << bucket(10, 7) << '\n';
    cout << "b5=" << bucket(12, 5) << '\n';
    return 0;
}
