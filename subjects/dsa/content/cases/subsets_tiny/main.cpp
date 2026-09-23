// 第一题：子集。选或不选，回来要撤销。
#include <iostream>
#include <vector>

using namespace std;

vector<int> a = {1, 2};
vector<vector<int>> out;

// TODO(学员)：从下标 i 起做选择。骨架已写出口；你补「选 / 不选」。
void dfs(int i, vector<int>& path) {
    if (i == (int)a.size()) {
        out.push_back(path);
        return;
    }
    (void)path;
    // TODO: 选 a[i]：path.push_back，递归 i+1，再 pop
    // TODO: 不选 a[i]：直接递归 i+1
}

void print_sets() {
    cout << "n=" << out.size() << '\n';
}

// —— 以下驱动请勿改 ——
int main() {
    vector<int> path;
    dfs(0, path);
    print_sets();
    return 0;
}
