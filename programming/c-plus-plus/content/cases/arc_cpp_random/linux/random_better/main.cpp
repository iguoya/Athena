#include <random>
#include <functional>
#include <limits>
#include <iostream>
#include <vector>

using namespace std;

int main() {

    vector<int> sample(100);
//    default_random_engine e(random_device{}());
    default_random_engine e(0);
    uniform_int_distribution<unsigned> u(1, 1000);
    int i = 1;
    for(auto &m: sample) {
        m = u(e);
        cout<<m<<"\t";
    }
    cout<<endl;
    for(auto m: sample) {
        cout<<m<<"\t";
    }
}
