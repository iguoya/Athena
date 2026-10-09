// 第一题：先序 = 根、左、右。小树先走通。
#include <iostream>

using namespace std;

struct Node {
    int val;
    Node* left;
    Node* right;
};

// TODO(学员)：先序打印，结点之间一个空格，末尾不要多余空格也可，驱动会看数字顺序。
void preorder(Node* r) {
    if (!r) return;
    // TODO: 打印 r->val，再递归左、右（相邻数字用空格隔开）
    (void)r;
}

// —— 以下驱动请勿改 ——
int main() {
    Node n2{2, nullptr, nullptr};
    Node n3{3, nullptr, nullptr};
    Node n1{1, &n2, &n3};
    cout << "pre=";
    preorder(&n1);
    cout << '\n';
    return 0;
}
