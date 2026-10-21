#include <iostream>
#include <vector>
#include <algorithm>
#include <functional>
#include <string>
using namespace std;

double eval(std::function<double(double)> f, double x = 2.0){return f(x);}
int main()
{
    cout << "Hello World!" << endl;

    vector<int> vv = {50, -10, 20, -30, 7 , 9, 2};
    std::sort(vv.begin(), vv.end());
    for_each(vv.cbegin(), vv.cend(), [](int x){cout<<x<<"\t";});

    sort(vv.begin(), vv.end(), [](int x, int y) {
        return x > y;
    });
    cout<<endl;
     for_each(vv.cbegin(), vv.cend(), [](int x){cout<<x<<"\t";});



    auto printHello = []{ cout<<"Hello 虎子"<<endl; };
    cout<<printHello<<"addr:"<<&printHello<<endl;
    printHello();


//    auto add = [](int a, int b) -> int { return a*a + b*b; };

    std::vector<int> some_list;
    int total = 0;
    for (int i=0;i<5;++i) some_list.push_back(i);
    for_each(begin(some_list), end(some_list), [&total](int x)
    {
        total += x;
    });
    cout<<total<<endl;


    std::function<double(double)> f0    = [](double x){return 1;};
    auto                          f1    = [](double x){return x;};
    decltype(f0)                  fa[3] = {f0,f1,[](double x){return x*x;}};
    std::vector<decltype(f0)>     fv    = {f0,f1};
    fv.push_back([](double x){return x*x;});
    for(int i=0;i<fv.size();i++)
        std::cout << fv[i](2.0) << "\n";

    cout<<"\n------------------\n";
    auto fp = [](int x)->int {
        return x+100;
    };

    cout<<fp(5)<<endl;
    auto fp2 = [](int x)->int {
        return x*x;
    };



//    auto fp3 = []() ->string {
//        return "hello";
//    };

//    auto fp4 = []() ->string {
//        return "world";
//    };

//    auto fp5 = [](int a, int b = 10) ->int {
//        return a+b;
//    };


    vector<decltype(fp)> fps;
    fps.push_back(fp);
//    fps.push_back(fp2);
//    fps.push_back(fp3);
//    fps.push_back(fp4);
//    fps.push_back(fp5);


    for(auto i = 0; i< fps.size(); ++i) {
        cout<<fps[i](i)<<endl;
    }

    auto basicLambda = [] { cout << "Hello, world!" << endl; };
    // 调用
    basicLambda();   // 输出：Hello, world!

    auto add = [](int a, int b) -> int { return a + b; };
    // 自动推断返回类型
    auto multiply = [](int a, int b) { return a * b; };

    int sum = add(2, 5);   // 输出：7
    int product = multiply(2, 5);  // 输出：10


    int x = 10;

    auto add_x = [x](int a) { return a + x; };  // 复制捕捉x
    auto multiply_x = [&x](int a) { return a * x; };  // 引用捕捉x

    cout << add_x(10) << " " << multiply_x(10) << endl;

    int x1 = 10;

    auto add_x1 = [&](int a)  mutable{ x1 *= 2; return a + x1; };  // 复制捕捉x

    cout<<x1<<endl;

    cout << add_x1(10) << endl; // 输出 30


    int value = 1;
    vector<int> v {1, 3, 5, 2, 6, 10};

    int count = std::count_if(v.begin(), v.end(), [value](int x) { return x > value; });
    cout<<count<<endl;


    std::function<bool(int, int)> wrapper = [](int x, int y) { return x < y; };

    cout<<wrapper(5, 2)<<endl;


    vector<long> v5(50);
     long a = 0;
     long b = 1;
    std::generate(v5.begin(), v5.end(), [&a, &b] {
        auto value = b;
        b = b + a;
        a = value;
        return value;
    });
    for_each(begin(v5), end(v5), [](int x){
         cout<<x<<"\t";
    });

//    for(int i=0;i<3;i++)
//        std::cout << fa[i](2.0) << "\n";
//    for(auto &f : fv)
//        std::cout << f(2.0) << "\n";
//    for(auto &f : fa)
//        std::cout << f(2.0) << "\n";
//    std::cout << eval(f0) << "\n";
//    std::cout << eval(f1) << "\n";

//    cout<<add(5, 7)<<endl;

    return 0;
}
