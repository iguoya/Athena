#include <cmath>
#include <iostream>
// #include <ctime>
using namespace std;

int main()
{

    std::cout << "Tiger's Project !" << std::endl;
    cout << "测试浮点:" << endl;
    cout << "---------------------------" << endl;
    float a = 123456789123456789.8888888888;
    float b = 123456789123456789.8888888888;
    cout << a * b << endl;
    double a1 = 123456789123456789.8888888888;
    double b1 = 123456789123456789.8888888888;
    cout << a1 * b1 << endl;

    //    数字定义
    float s = 3.1416 / 6;
    int i = -1000;
    long l = 10000;
    float f = 230.47;
    double d = 25.000;

    cout << "数学运算" << endl;
    cout << "---------------------------" << endl;
    cout << "sin(s) :" << sin(s) << endl;
    cout << "abs(i)  :" << abs(i) << endl;
    cout << "floor(f) :" << floor(f) << endl;
    cout << "sqrt(l) :" << sqrt(l) << endl;
    cout << "pow( d, 2) :" << pow(d, 2) << endl;

    cout << "随机数" << endl;
    cout << "---------------------------" << endl;
    srand(time(NULL));

    cout << "取值范围:[1, 100]"<< endl;
    for (size_t i = 1; i <= 100; ++i)
    {
        cout << rand() % (100-1+1)+1 << "\t";
        if(i%10 == 0) {
            cout << endl;
        }
    }
    cout << "取值范围:[11,77]" << endl;
    for (size_t i = 1; i <= 100; ++i)
    {
        cout << rand() % (77-11+1)+11 << "\t";
        if(i%10 == 0) {
            cout << endl;
        }
    }



//    cout << "包含1,100" << endl;
//         for (size_t i = 1; i <= 100; ++i) {
        
//         cout << rand() % (100+1) << "\t";
//         if(i%10 == 0) {
//             cout << endl;
//         }
//     }
// cout << "包含1,100" << endl;
//     for (size_t i = 1; i <= 100; ++i) {
        
//         cout << rand() % (100+1) << "\t";
//         if(i%10 == 0) {
//             cout << endl;
//         }
//     }


    return 0;
}
