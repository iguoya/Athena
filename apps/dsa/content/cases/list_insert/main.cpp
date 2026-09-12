// 第一题：已知结点后面插入。改指针，不要找第 k 个。
#include <iostream>

using namespace std;

struct Node {
    int val;
    Node* next;
};

// TODO(学员)：在 p 后面插入值为 x 的新结点。p 保证非空。
void insert_after(Node* p, int x) {
    (void)p;
    (void)x;
    // TODO: Node* q = new Node{x, p->next}; p->next = q;
}

void print_list(Node* h) {
    for (Node* p = h; p; p = p->next) {
        cout << p->val;
        if (p->next) cout << ' ';
    }
    cout << '\n';
}

// —— 以下驱动请勿改 ——
int main() {
    Node* a = new Node{1, nullptr};
    Node* c = new Node{3, nullptr};
    a->next = c;
    insert_after(a, 2);
    cout << "list=";
    print_list(a);
    return 0;
}
