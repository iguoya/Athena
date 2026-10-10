// 情境：手写资源管理却漏了默认操作。Scores 用 new[] 自己管一块数组，但既没写析构函数，
// 也没写拷贝构造——编译器生成的拷贝只复制指针（浅拷贝），两个对象共享同一块内存：
// 改了副本，原件跟着变；而且这块内存从来没人释放。
// 组织手段：零法则——能不定义默认操作就不定义，让成员（std::vector、std::string、智能指针）
// 自己管理资源；确实要自己管，就五个特殊成员函数一起定义或一起删除（五法则）。
// 规范：C++ Core Guidelines C.20「能避免定义默认操作就避免」、
// C.21「定义或删除了任何一个拷贝、移动或析构函数，就把它们全部定义或删除」。
//
// 实验：
// 1. 把 int* data_ 与 size_ 换成 std::vector<int> data_；构造函数改为 data_(n, init)。
// 2. 不写析构、拷贝、移动——零法则。at() 与 size() 改为基于 vector。
// 3. 运行后应输出 original[0]=1 copy[0]=99：副本是独立的。
#include <iostream>

// TODO(实验)：把 int* data_ 换成 std::vector<int>，不写任何特殊成员函数
class Scores {
public:
    Scores(int n, int init) : data_(new int[n]), size_(n) {
        for (int i = 0; i < n; ++i) data_[i] = init;
    }
    int& at(int i) { return data_[i]; }
    int size() const { return size_; }
private:
    int* data_;   // 没有析构函数：泄漏；默认拷贝只复制指针：共享
    int size_;
};

int main() {
    Scores original(3, 1);
    Scores copy = original;   // 以为得到了一份独立的副本
    copy.at(0) = 99;
    std::cout << "original[0]=" << original.at(0) << " copy[0]=" << copy.at(0) << "\n";
}
