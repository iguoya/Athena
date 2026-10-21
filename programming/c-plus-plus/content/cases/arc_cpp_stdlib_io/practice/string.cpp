#include <iostream>
#include <string>
#include <iomanip>
using namespace std;

int main()
{
    // setlocale(LC_ALL,"");
    //setlocale(LC_ALL, "zh_CN.UTF-8");
    //  setlocale(LC_CTYPE,"");
    char greeting[6] = {'H', 'e', 'l', 'l', 'o', '\0'};

    cout << "Greeting message: ";
    cout << greeting << endl;
    // wchar_t yulai[] = L"我们是中国人，我们爱自己的祖国。";
    // cout << wcslen(yulai) << endl;
    // cout << sizeof(yulai) << endl;
    // wcout << yulai << endl;

    // 复制
    string str1 = "我们是中国人";
    string copy_str1 = str1;
    cout << "一起喊:"
         << str1 << endl
         << copy_str1 << endl;
    string str2 = "我们爱自己的祖国";
    string yulai_says = str1 + "，" + str2 + "。";
    cout << "雨来说:" << yulai_says << endl;
    cout << "总共"
         << str1.size()
         <<"+"
         << str2.size()
         << "个字" << endl;
         



    return 0;
}
