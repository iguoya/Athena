// 情境：全局数据与可变数据。g_requestCount 是一个任何函数都能改的全局变量。
// 新需求来了：一个进程里要同时统计两个独立会话的请求数——全局变量只有一份，做不到。
// 重构手法：封装变量（Encapsulate Variable），《重构》第 2 版。
// 规范：C++ Core Guidelines I.2「避免非 const 的全局变量」、Con.1「默认让对象不可变」。
//
// 实验：
// 1. 写 class Session：私有成员 int count_ = 0；提供 void record() 与 int count() const。
// 2. 删掉全局变量与 handleRequest()，解开 main 里的 TODO(实验) 段——两个会话各数各的。
//    达标时会输出 a=2 b=1。
#include <iostream>

int g_requestCount = 0;   // 谁都能改；一个进程只有一份

void handleRequest() {
    ++g_requestCount;
}

int main() {
    handleRequest();
    handleRequest();
    handleRequest();
    std::cout << "requests=" << g_requestCount << "\n";

    // TODO(实验)：写好 Session 后，解开下面这段
    // Session a, b;
    // a.record();
    // a.record();
    // b.record();
    // std::cout << "a=" << a.count() << " b=" << b.count() << "\n";
}
