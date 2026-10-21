#include <iostream>
#include <vector>

using namespace std;

void footstep(int n, vector<int> route, vector<vector<int>> &result) {
    if (n > 0) {

        route.push_back(1);
        footstep(n-1, route, result);
        route.pop_back();

        route.push_back(2);
        footstep(n-2, route, result);
        route.pop_back();

        route.push_back(3);
        footstep(n-3, route, result);
        route.pop_back();

    } else if(n == 0) {
        result.push_back(route);
    } else {

    }
}

int main() {
    std::cout << "Hello, World!" << std::endl;
    vector<int> route;
    vector<vector<int>> result;
    footstep(10,route, result);

    for(auto route: result) {
        for(auto node: route) {
            cout<<node<<"\t";
        }
        cout<<endl;
    }
    return 0;
}
