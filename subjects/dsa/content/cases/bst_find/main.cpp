// 第一题：BST 查找。左小右大，一次只走一边。
#include <iostream>

using namespace std;

struct Node {
    int val;
    Node* left;
    Node* right;
};

// TODO(学员)：树中是否存在 x。
bool contains(Node* r, int x) {
    (void)r;
    (void)x;
    return false; // TODO: 空则否；相等则是；否则按大小走左或右
}

// —— 以下驱动请勿改 ——
int main() {
    Node n2{2, nullptr, nullptr};
    Node n6{6, nullptr, nullptr};
    Node n4{4, &n2, &n6};
    cout << "has2=" << (contains(&n4, 2) ? 1 : 0) << '\n';
    cout << "has5=" << (contains(&n4, 5) ? 1 : 0) << '\n';
    cout << "has4=" << (contains(&n4, 4) ? 1 : 0) << '\n';
    return 0;
}
