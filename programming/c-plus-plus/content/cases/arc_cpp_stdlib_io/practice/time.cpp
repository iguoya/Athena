#include <iostream>
#include <ctime>
 
using namespace std;
 
int main( )
{
   // 基于当前系统的当前日期/时间
   time_t now = time(0);
   
   // 把 now 转换为字符串形式
   char* dt = ctime(&now);
 
   cout << "本地日期和时间：" << dt << endl;
 
   // 把 now 转换为 tm 结构
   tm *gmtm = gmtime(&now); 
   dt = asctime(gmtm);
   cout << "UTC 日期和时间："<< dt << endl;

      // 基于当前系统的当前日期/时间
   time_t current_time = time(0);
 
   cout << "1970 到目前经过秒数:" << current_time << endl;
 
   tm *ltm = localtime(&current_time);
 
   // 输出 tm 结构的各个组成部分
   cout << "年: "<< 1900 + ltm->tm_year << endl;
   cout << "月: "<< 1 + ltm->tm_mon<< endl;
   cout << "日: "<<  ltm->tm_mday << endl;
   cout << "时间: "<< ltm->tm_hour << "时"<<endl;
   cout << ltm->tm_min << "分"<<endl;
   cout << ltm->tm_sec <<"秒"<< endl;
}