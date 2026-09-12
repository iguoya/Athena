// 数组代价体感：尾插 vs 中部插入（用搬移次数近似）。
#include <cstdint>
#include <iostream>
#include <vector>

using namespace std;

struct Counter {
    uint64_t moves = 0;
};

// 在 index 处插入，模拟「从末尾挪到 index」的赋值次数。
void insert_at(vector<int>& a, size_t index, int value, Counter& c) {
    a.push_back(0);
    for (size_t i = a.size() - 1; i > index; --i) {
        a[i] = a[i - 1];
        ++c.moves;
    }
    a[index] = value;
}

int main() {
    constexpr int n = 1000;

    Counter tail;
    vector<int> a;
    a.reserve(n);
    for (int i = 0; i < n; ++i) {
        a.push_back(i); // 尾插：均摊 O(1)，这里不计扩容细节
    }
    cout << "tail_push n=" << n << " moves≈0 (未计扩容)\n";

    Counter mid;
    vector<int> b;
    b.reserve(n);
    for (int i = 0; i < n; ++i) {
        insert_at(b, 0, i, mid); // 每次插到头部 → 搬移越来越多
    }
    cout << "head_insert n=" << n << " moves=" << mid.moves
         << "  (约 n(n+1)/2)\n";

    cout << "结论：同样 n 次插入，位置不同，搬移量差一个数量级形态。\n";
    return 0;
}
