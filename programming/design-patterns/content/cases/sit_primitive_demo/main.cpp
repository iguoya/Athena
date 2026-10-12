// 情境：基本类型偏执。金额用 double 表示，币种另用一个字符串跟着——两笔不同币种的钱
// 也能直接相加，编译器毫无察觉；而且 0.1 + 0.2 这类浮点误差会混进账目。
// 重构手法：以对象取代基本类型（Replace Primitive with Object），《重构》第 2 版。
// 规范：C++ Core Guidelines I.4「接口要精确且强类型」。
//
// 实验：
// 1. 写一个 class Money：内部用 long long 存「分」，外加币种 std::string currency；
//    构造函数 Money(long long cents, std::string currency)。
// 2. 提供 Money operator+(const Money&) const：币种不同时抛 std::invalid_argument("currency mismatch")。
// 3. 提供 std::string str() const，格式如 120.50 CNY（两位小数）。
// 4. 解开 main 里的 TODO(实验) 段。达标时会输出 120.50 CNY 与 error: currency mismatch。
#include <iostream>
#include <stdexcept>
#include <string>

int main() {
    double price = 100.0;        // 人民币
    double shipping = 20.5;      // 人民币
    double refund = 15.0;        // 美元——但类型上看不出来
    std::cout << "total: " << price + shipping + refund << "\n";   // 不同币种混加，编译器不拦

    // TODO(实验)：写好 Money 后解开下面这段
    // Money a(10000, "CNY"), b(2050, "CNY"), c(1500, "USD");
    // std::cout << (a + b).str() << "\n";
    // try {
    //     std::cout << (a + c).str() << "\n";
    // } catch (const std::invalid_argument& e) {
    //     std::cout << "error: " << e.what() << "\n";
    // }
}
