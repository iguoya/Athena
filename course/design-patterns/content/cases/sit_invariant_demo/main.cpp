// 情境：不变式没人守。DateRange 要求 begin <= end，但成员是公开的，谁都能把它改成
// 「结束早于开始」，后面每个用到它的函数都得自己再检查一遍——或者忘了检查。
// 组织手段：有不变式的就用 class——成员私有，构造函数检查并建立不变式，
// 之后只通过保持不变式的成员函数修改。
// 规范：C++ Core Guidelines C.2「有不变式用 class，成员可以独立变化用 struct」、
// C.41「构造函数应创建一个完全初始化的对象」、C.9「尽量少暴露成员」。
//
// 实验：
// 1. 把 struct DateRange 改成 class：begin_、end_ 私有；构造函数 DateRange(int begin, int end)
//    在 end < begin 时抛 std::invalid_argument("end before begin")。
// 2. 提供 int length() const 返回 end_ - begin_。
// 3. 删掉 main 里的旧代码，解开 TODO(实验) 段。达标时会输出
//    rejected: end before begin 与 length=5。
#include <iostream>
#include <stdexcept>

struct DateRange {
    int begin;   // 第几天
    int end;     // 要求 begin <= end，但没人保证
};

int length(const DateRange& r) { return r.end - r.begin; }

int main() {
    DateRange r{3, 8};
    r.end = 1;   // 任何代码都能把它改坏
    std::cout << "length=" << length(r) << "\n";

    // TODO(实验)：改成 class 之后，删掉上面三行，解开下面这段
    // try {
    //     DateRange bad(10, 3);
    //     std::cout << "length=" << bad.length() << "\n";
    // } catch (const std::invalid_argument& e) {
    //     std::cout << "rejected: " << e.what() << "\n";
    // }
    // DateRange ok(3, 8);
    // std::cout << "length=" << ok.length() << "\n";
}
