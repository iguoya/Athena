// 情境：接口表达不出契约。parseTime() 靠返回 bool + 三个输出指针传结果：调用方得先声明三个
// 变量、传进地址；失败时指针里是什么没人知道；三个 int 谁是时、谁是分、谁是秒，全凭参数顺序。
// 规范：C++ Core Guidelines I.1 接口要显式、I.4 接口要精确且强类型、F.20 输出值优先用
// 返回值而不是输出参数、F.21 多个输出值就返回结构体。
//
// 实验：
// 1. 定义 struct Time { int hour; int minute; int second; }。
// 2. 把 parseTime 改成 std::optional<Time> parseTime(const std::string&)：
//    解析失败返回 std::nullopt，成功返回值；不再有输出指针。
// 3. 新需求：写 Time addSeconds(Time, int)（秒数可以跨过整点，不跨天），
//    以及 std::string format(const Time&)，输出 HH:MM:SS（补零）。
// 4. 解开 main 里的 TODO(实验) 行。达标时会输出
//    t=12:30:05 / t=invalid / plus 1800s = 13:00:05。
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

// 成功返回 true，并写入 h / m / s；失败返回 false，此时三个指针里的值不可依赖。
bool parseTime(const std::string& text, int* h, int* m, int* s) {
    char c1 = 0, c2 = 0;
    std::istringstream in(text);
    if (!(in >> *h >> c1 >> *m >> c2 >> *s)) return false;
    if (c1 != ':' || c2 != ':') return false;
    return *h >= 0 && *h < 24 && *m >= 0 && *m < 60 && *s >= 0 && *s < 60;
}

int main() {
    for (const char* text : {"12:30:05", "25:00:00"}) {
        int h = 0, m = 0, s = 0;
        if (parseTime(text, &h, &m, &s))
            std::cout << "ok " << std::setfill('0') << std::setw(2) << h << ":" << std::setw(2) << m << ":" << std::setw(2) << s << "\n";
        else
            std::cout << "invalid\n";
    }
    // TODO(实验)：改好 parseTime()、写好 addSeconds() 与 format() 后，把上面的循环换成下面几行
    // for (const char* text : {"12:30:05", "25:00:00"}) {
    //     auto t = parseTime(text);
    //     std::cout << "t=" << (t ? format(*t) : std::string("invalid")) << "\n";
    // }
    // std::cout << "plus 1800s = " << format(addSeconds(*parseTime("12:30:05"), 1800)) << "\n";
}
