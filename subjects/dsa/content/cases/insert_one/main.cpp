// 第一题：往有序前缀里插入一个数（插入排序的一步）。
#include <iostream>
#include <vector>

using namespace std;

// TODO(学员)：a 已按升序排好，把 x 插进去后仍有序。
void insert_sorted(vector<int>& a, int x) {
    (void)a;
    (void)x;
    // TODO: 从尾部找位置，大于 x 的右移，再写入 x
}

void print_vec(const vector<int>& a) {
    for (size_t i = 0; i < a.size(); ++i) {
        if (i) cout << ',';
        cout << a[i];
    }
    cout << '\n';
}

// —— 以下驱动请勿改 ——
int main() {
    vector<int> a = {1, 3, 7, 9};
    insert_sorted(a, 4);
    cout << "a=";
    print_vec(a);
    return 0;
}
