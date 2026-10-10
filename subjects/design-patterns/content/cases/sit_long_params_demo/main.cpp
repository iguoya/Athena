// 情境：过长参数列表与数据泥团。bookRoom() 有 7 个参数：年、月、日总是一起出现（数据泥团），
// 两个 bool 让调用处只剩一串 true/false（标记参数），调用者很容易把顺序写错。
// 重构手法：引入参数对象（Introduce Parameter Object）、移除标记参数（Remove Flag Argument），
// 《重构》第 2 版。规范：C++ Core Guidelines I.23「函数参数要少」、I.4「接口要精确且强类型」。
//
// 实验：
// 1. 定义 struct Date { int year, month, day; }; 与 struct Stay { Date checkIn; int nights; };
// 2. 定义 struct Extras { bool breakfast = false; bool lateCheckout = false; };
// 3. 写新的 bookRoom(const std::string& guest, const Stay& stay, const Extras& extras)，
//    输出格式与旧版相同。解开 main 里的 TODO(实验) 段（它用了 C++20 的指定初始化，
//    一眼就能看出每个值是什么）。达标时会输出 wang 2026-10-03 x1 [late-checkout]。
#include <iostream>
#include <string>

void bookRoom(const std::string& guest, int year, int month, int day, int nights,
              bool breakfast, bool lateCheckout) {
    std::cout << guest << " " << year << "-" << (month < 10 ? "0" : "") << month << "-"
              << (day < 10 ? "0" : "") << day << " x" << nights
              << (breakfast ? " [breakfast]" : "") << (lateCheckout ? " [late-checkout]" : "") << "\n";
}

int main() {
    bookRoom("li", 2026, 10, 1, 3, true, false);   // 第 5、6、7 个参数分别是什么？

    // TODO(实验)：定义好 Date、Stay、Extras 和新的 bookRoom 后，解开下面两行
    // bookRoom("li", Stay{.checkIn = {2026, 10, 1}, .nights = 3}, Extras{.breakfast = true});
    // bookRoom("wang", Stay{.checkIn = {2026, 10, 3}, .nights = 1}, Extras{.lateCheckout = true});
}
