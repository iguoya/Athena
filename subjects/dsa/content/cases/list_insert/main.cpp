// 第一题：已知结点后面插入。改指针，不要找第 k 个。
#include <iostream>
#include <vector>

#include "dsa_trace.hpp"

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

// 从链表真实取样：trace 帧必须是真实状态，不是预期的剧本（本应用 ADR 0004）。
// 没实现 insert_after 时，插入后的快照会如实显示 1 -> 3。
vector<int> list_values(const Node* h) {
    vector<int> vs;
    for (const Node* p = h; p; p = p->next) vs.push_back(p->val);
    return vs;
}

// —— 以下驱动请勿改 ——
int main() {
    Node* a = new Node{1, nullptr};
    Node* c = new Node{3, nullptr};
    a->next = c;
    dsa_trace::list(0, "初始链表 1 -> 3", list_values(a), -1);
    dsa_trace::list(1, "调用 insert_after(a, 2)：在结点 1 后面接一个值为 2 的新结点", list_values(a), 0);
    insert_after(a, 2);
    dsa_trace::list(2, "插入后的链表：新结点 2 应该接在 1 和 3 中间", list_values(a), 1);
    cout << "list=";
    print_list(a);
    return 0;
}
