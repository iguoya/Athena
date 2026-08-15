#include "time.h"

Time::Time()
{

}

void Time::run()
{
    // 基于当前系统的当前日期/时间
    time_t now = time(nullptr);

    // 把 now 转换为字符串形式

    display(format("本地日期和时间： %s",  ctime(&now)));

    // 把 now 转换为 tm 结构
    tm *gmtm = gmtime(&now);
    display(format("UTC 日期和时间： %s",  asctime(gmtm)));

    // 基于当前系统的当前日期/时间
    time_t current_time = time(nullptr);
    display(format("1970 到目前经过秒数: %ld",  current_time));

    tm *ltm = localtime(&current_time);

    // 输出 tm 结构的各个组成部分
    display(format("%d 年  %d 月 %d 日   %d 时 %d 分 %d 秒",
                   1900 + ltm->tm_year,
                   1 + ltm->tm_mon,
                   ltm->tm_mday,
                   ltm->tm_hour,
                   ltm->tm_min,
                   ltm->tm_sec
                   ));
}
