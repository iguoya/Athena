// 第二题：从头走到尾数结点。定位是 O(n)，先有体感。
#include <iostream>

using namespace std;

struct Node {
    int val;
    Node* next;
};

// TODO(学员)：返回链表长度（空表为 0）。
int length(Node* head) {
    (void)head;
    return 0; // TODO: 沿 next 走并计数
}

// —— 以下驱动请勿改 ——
int main() {
    Node* c = new Node{3, nullptr};
    Node* b = new Node{2, c};
    Node* a = new Node{1, b};
    cout << "len0=" << length(nullptr) << '\n';
    cout << "len3=" << length(a) << '\n';
    return 0;
}
