#include <iostream>

using namespace std;

constexpr int func2() {
    return 10;
}

int main()
{
    cout << "Hello World!" << endl;
    using dnum2 = double;
    using pstring2 = char*;

//    using func2 = int(int);
    using pfunc2 = int(*)(int);

    using arr2 = int[10];
    using parr2 = int(*)[10];
    using tparr2 = int(&)[10];

    arr2 b{5, 7};
    for(auto m: b) {
        cout<<m<<"\t";
    }
    cout<<endl;

    const int ci = 0, &cj = ci;
    decltype(ci) x = 0;
    decltype(cj) y = x;
//    decltype(cj) z; //报错，因为cj是一个引用，因此作为引用的 z 必须要进行初始化

    int arr[func2() + 10] = {0};
    for(auto i : arr) {
        cout<<i<<"\t";
    }

    std::cout << "Hello, World!" << std::endl;
    return 0;
}
