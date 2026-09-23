// 第二题：BFS 访问顺序。队列 + visited。无权最短的骨架。
#include <iostream>
#include <queue>
#include <vector>

using namespace std;

// TODO(学员)：从 s 做 BFS，按访问顺序把结点编号写入 order。
void bfs(const vector<vector<int>>& g, int s, vector<int>& order) {
    order.clear();
    (void)g;
    (void)s;
    // TODO: 队列推进，入队前标记 visited
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
    vector<vector<int>> g(4);
    g[0] = {1, 2};
    g[1] = {0, 3};
    g[2] = {0};
    g[3] = {1};
    vector<int> order;
    bfs(g, 0, order);
    cout << "bfs=";
    print_vec(order);
    return 0;
}
