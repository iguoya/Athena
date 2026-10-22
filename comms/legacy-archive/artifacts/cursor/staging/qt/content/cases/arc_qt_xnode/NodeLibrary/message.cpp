#include "message.h"

//size_t Log::count;

Log::Log(std::string source, size_t number)
{
//    ++count;
//    number = count;
    this->number = number;
    this->source = source;
    setTime();
}

void Log::setTime()
{
//    struct timeval time_now{};
//    gettimeofday(&time_now, nullptr);
//    time_t msecs_time = (time_now.tv_sec * 1000) + (time_now.tv_usec / 1000);

//    cout << "seconds since epoch: " << time_now.tv_sec << endl;
//    cout << "milliseconds since epoch: "  << msecs_time << endl << endl;

    auto now = std::chrono::system_clock::now();
    //通过不同精度获取相差的毫秒数
    uint64_t dis_millseconds = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count()
        - std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count() * 1000;
    time_t tt = std::chrono::system_clock::to_time_t(now);
    auto time_tm = localtime(&tt);
    char strTime[25] = { 0 };
    sprintf(strTime, "%d-%02d-%02d %02d:%02d:%02d.%03d", time_tm->tm_year + 1900,
        time_tm->tm_mon + 1, time_tm->tm_mday, time_tm->tm_hour,
        time_tm->tm_min, time_tm->tm_sec, (int)dis_millseconds);
    time.assign(strTime);
}


void Log::setMessage(std::string message)
{
    this->message.assign(message);
}
