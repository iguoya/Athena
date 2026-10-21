#include <iostream>
#include <vector>
#include <list>
#include <string>
using namespace std;

template <typename T>
void permutation(list<T> sample, vector<T> route, vector<vector<T>> &result) {
    if(sample.size() == 0) {
        result.push_back(route);
    } else {
        for(auto it = sample.begin(); it != sample.end(); ++it) {
            route.push_back(*it);
            list<T> se_sample(sample);
            se_sample.remove(*it);
            permutation(se_sample, route, result);
            route.pop_back();
        }
    }
}

template <typename T>
void show(vector<vector<T>> &result) {
    for(const auto &route: result) {
        for(const auto &node: route) {
            cout<<node<<"\t";
        }
        cout<<endl;
    }
    cout<<endl;
}

int main() {
    std::cout << "Hello, World!" << std::endl;
    vector<vector<int>> result;
    list<int> sample;
    vector<int> route;

    for(int i = 1; i < 5; ++i) {
        sample.push_back(i);
    }
    permutation(sample, route, result);
    show(result);
//    result.erase();
//    cout<<"is empty ??"<<endl;
//    show(result);
//    cout<<"empty!!!"<<endl;
//ddd


    vector<vector<string>> result2;
    list<string> sample2 = {"I", "love", "china's", "history"};
    vector<string> route2;
    permutation(sample2, route2, result2);
    show(result2);


    return 0;
}
