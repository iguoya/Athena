#include <iostream>
#include <cstdlib>
#include <vector>
using namespace std;

size_t subValue(int m, int n) {
    return m*n - rand()%100;
}

size_t addValue(int m, int n) {
    return rand()%100+m*n;
}


void doSth(vector<size_t> &nums, size_t (*func)(int, int), int m, int n) {
    for(int i =0; i < 100; ++i) {
        nums.push_back(func(m, n));
    }
}

int main() {
    std::cout << "Hello, World!" << std::endl;
    vector<size_t> nums;
//    size_t (*func)(int, int) = setValue;
    doSth(nums, addValue, 100, 100);
    for(auto m: nums) {
        cout<<m<<"\t";
    }
    nums.clear();
    cout<<endl;
    doSth(nums, subValue, 100, 10);
    for(auto m: nums) {
        cout<<m<<"\t";
    }

    return 0;
}