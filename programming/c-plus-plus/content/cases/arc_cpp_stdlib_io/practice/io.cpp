#include <iostream>

using namespace std;

int main()
{
    char str[] = "Hello C++";

    cout << "Value of str is : " << str << endl;

    // string name;
    // string age;

    // cout << "请输入您的姓名,年龄： ";
    // cin >> name >> age;
    // cout << "您是： " << name << endl;
    string err = "发生了错误....";
     cerr << "Error message : " << str << endl;
     string log = "记录一个日志.....";
     clog <<"日志类型:"<< log << endl;
}