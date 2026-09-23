// 第一题：无向图加边。邻接表两端都记。
#include <iostream>
#include <vector>

using namespace std;

// TODO(学员)：在无向图 g 的 u、v 之间加一条边。
void add_undirected(vector<vector<int>>& g, int u, int v) {
    (void)g;
    (void)u;
    (void)v;
    // TODO: g[u].push_back(v); g[v].push_back(u);
}

void print_deg(const vector<vector<int>>& g) {
    for (size_t i = 0; i < g.size(); ++i) {
        if (i) cout << ',';
        cout << g[i].size();
    }
    cout << '\n';
}

// —— 以下驱动请勿改 ——
int main() {
    vector<vector<int>> g(3);
    add_undirected(g, 0, 1);
    add_undirected(g, 0, 2);
    cout << "deg=";
    print_deg(g);
    return 0;
}
