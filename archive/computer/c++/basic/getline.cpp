#include "getline.h"

Getline::Getline()
{

}

void Getline::run()
{
    time_t current_time = time(0);
    tm *ltm = localtime(&current_time);
    display(to_string(1900+ltm->tm_year)+"年" + to_string(ltm->tm_mon) +"月"+ to_string(ltm->tm_mday)+"日");

    std::ostringstream   oss;
    oss << 1900 + ltm->tm_year << "年" << ltm->tm_mon << "月" << ltm->tm_mday << "日";
    display(oss.str());

    //    cout << "请输入一行字符串:" << endl;
    //    string str;
    //    // cin >> str;
    //    getline(cin, str);

    //    cout << "你输入的是:" << endl;
    //    cout << str << endl;

    //    vector<string> words;

    //    split(str, words);
    //    for (auto it = words.begin(); it != words.end(); ++it)
    //    {
    //        cout<< *it << endl;
    //    }
    // to do
    // 提取字符串
    //比较字符串
    // 添加字符串
    // 搜索字符串
}
