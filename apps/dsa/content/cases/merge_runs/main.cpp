// 归并的一步：两段有序合成一段。分治的「合」。
#include <iostream>
#include <vector>

using namespace std;

// TODO(学员)：a、b 升序，把合并结果写入 out（调用方已准备好容量）。
void merge_sorted(const vector<int>& a, const vector<int>& b, vector<int>& out) {
    out.clear();
    (void)a;
    (void)b;
    // TODO: 双指针从小到大写入 out
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
    vector<int> a = {1, 4, 7};
    vector<int> b = {2, 3, 8};
    vector<int> out;
    merge_sorted(a, b, out);
    cout << "m=";
    print_vec(out);
    return 0;
}
