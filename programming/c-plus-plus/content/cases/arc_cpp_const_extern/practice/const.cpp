#include <iostream>
using namespace std;
class A
{
private:
    int a;

public:
    A()
    {
        cout << "const constructor" << endl;
    }
    void f1(int arg) const // 常成员函数
    {
        cout << "variable :";
        cout << arg << endl;
        // a = 100; //!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        cout << a << endl;
    }
    void f2(const int i)
    {
        // i = 10000;//error  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        cout << i << endl;
    }
};

int main()
{
    /* const  用法灵活, 大大改善程序的健壮性 */

    // 情况1 : const 常量
    const int a = 1;

    // a = 2; !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    cout << a << endl;

    //情况2 : 类型检查
    A obj;
    obj.f1(1000);
    obj.f2(555);

    const char *p1 = "China";
    // *p1 = "Japan"; !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    cout << *p1 << endl;

    int i = 1000;
    int *const p2 = &i;
    cout << *p2 << endl;
    int j = 300;

    // p2 = &j;
    // cout << *p2 << endl;

    int *p3 = &j;
    cout << *p2 << endl;
    //
    *p2 = 888;

    cout << *p2 << endl;

    const A obj2;
    obj2.f1(999);
    // obj2.f2(666);// error !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
}