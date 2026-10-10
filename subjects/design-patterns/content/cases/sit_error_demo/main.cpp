// 情境：错误被悄悄吞掉。parsePort() 用返回值表示成败、用输出参数带回结果，
// 调用者忘了检查返回值，就拿着一个没被赋值的 port 继续往下走。
// 组织手段：让「可能没有结果」写进返回类型——std::optional 表示「有或没有」，
// 调用者不检查就拿不到值；无法完成任务、调用者通常也处理不了时再用异常。
// 规范：C++ Core Guidelines F.20「输出值优先用返回值而不是输出参数」、
// E.2「函数无法完成它的任务时抛异常」、E.3「异常只用于错误处理」；
// 重构手法：以异常取代错误码（Replace Error Code with Exception，《重构》第 2 版）。
//
// 实验：
// 1. 把 parsePort 改成 std::optional<int> parsePort(const std::string& s)：合法时返回端口，
//    非数字或不在 1–65535 范围内时返回 std::nullopt。
// 2. main 里对每个输入：有值输出 port=<值>，没有值输出 invalid port: <输入>。
// 3. 达标时会输出 port=8080 与 invalid port: abc。
#include <iostream>
#include <optional>
#include <string>
#include <vector>

// 返回 0 表示成功，-1 表示失败；结果通过 out 带回
int parsePort(const std::string& s, int& out) {
    if (s.empty()) return -1;
    int value = 0;
    for (char c : s) {
        if (c < '0' || c > '9') return -1;
        value = value * 10 + (c - '0');
        if (value > 65535) return -1;
    }
    if (value == 0) return -1;
    out = value;
    return 0;
}

int main() {
    std::vector<std::string> inputs{"8080", "abc"};
    for (const auto& s : inputs) {
        int port = 0;
        parsePort(s, port);              // 返回值被忽略了
        std::cout << "port=" << port << "\n";
    }
    // TODO(实验)：改成 std::optional 之后，按要求重写上面的循环
}
