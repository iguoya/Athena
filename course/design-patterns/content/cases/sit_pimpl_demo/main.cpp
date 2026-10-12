// 情境：头文件把实现细节全暴露了。Report 的私有成员有 std::vector、std::map……
// 使用者只想调用 add() 和 count()，却被迫 include 这些头；每次给 Report 加一个私有字段，
// 所有包含它的源文件都要重新编译。
// 规范：C++ Core Guidelines I.27（需要稳定的库 ABI 时考虑 Pimpl 惯用法）、
// SF.11（头文件自包含）；前向声明只能用于指针/引用，不能用于要知道大小的成员。
//
// 本文件用注释分隔模拟「头文件」与「源文件」两部分——真实项目里它们是 report.h 与 report.cpp。
// 实验：
// 1. 把「头文件」部分的私有成员全部收进 struct Impl（头文件部分只前向声明 struct Impl;），
//    类里只剩一个 std::unique_ptr<Impl> impl_。
// 2. Impl 的定义和所有成员函数、析构函数都放在「源文件」部分——析构函数必须在 Impl 定义
//    之后再写（= default 也行），想想为什么。
// 3. 在 Impl 里新增一个 int version 字段（不动「头文件」部分），add() 时自增；
//    再给 Report 补一个 int version() const。解开 main 里的 TODO(实验) 行。
//    达标时会输出 pimpl: yes 和 lines=2 version=2。
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>

// ======== report.h（使用者看到的部分） ========
class Report {
public:
    void add(const std::string& line) { lines_.push_back(line); ++byLength_[line.size()]; }
    int count() const { return static_cast<int>(lines_.size()); }
private:
    std::vector<std::string> lines_;
    std::map<std::size_t, int> byLength_;
};

// ======== report.cpp（实现者看到的部分） ========

int main() {
    Report r;
    r.add("hello");
    r.add("world");
    std::cout << "pimpl: " << (sizeof(Report) == sizeof(void*) ? "yes" : "no") << "\n";
    std::cout << "lines=" << r.count() << "\n";
    // TODO(实验)：改成 Pimpl、补好 version() 后，把上面的 lines= 那行换成下一行
    // std::cout << "lines=" << r.count() << " version=" << r.version() << "\n";
}
