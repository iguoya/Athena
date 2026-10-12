// 第二题：头插要搬家。n 很小，方便对着手算核对。
#include <cstdint>
#include <iostream>
#include <vector>

using namespace std;

struct Counter {
    uint64_t moves = 0;
};

// TODO(学员)：在 index 处插入 value。
// 约定：先 push_back 占位，再把 [index, end) 依次右移，并累加 c.moves。
void insert_at(vector<int>& a, size_t index, int value, Counter& c) {
    (void)a;
    (void)index;
    (void)value;
    (void)c;
    // TODO: 右移并写入
}

// —— 以下驱动请勿改 ——
int main() {
    constexpr int n = 10;

    vector<int> a;
    a.reserve(n);
    for (int i = 0; i < n; ++i) {
        a.push_back(i);
    }
    cout << "tail_push n=" << n << " moves≈0\n";

    Counter mid;
    vector<int> b;
    b.reserve(n);
    for (int i = 0; i < n; ++i) {
        insert_at(b, 0, i, mid);
    }
    cout << "head_insert n=" << n << " moves=" << mid.moves
         << "  (补全后约 n(n+1)/2=" << (uint64_t)n * (n + 1) / 2 << ")\n";
    return 0;
}
