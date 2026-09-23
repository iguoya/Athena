// 第一题：用 vector 模拟栈。只动栈顶。
#include <iostream>
#include <vector>

using namespace std;

// TODO(学员)：弹出栈顶并返回；调用方保证栈非空。
int pop_top(vector<int>& st) {
    (void)st;
    return 0; // TODO: 记下 st.back()，pop_back，再返回
}

// —— 以下驱动请勿改 ——
int main() {
    vector<int> st = {1, 2, 3};
    cout << "pop=" << pop_top(st) << '\n';
    cout << "pop=" << pop_top(st) << '\n';
    cout << "left=" << st.size() << '\n';
    return 0;
}
