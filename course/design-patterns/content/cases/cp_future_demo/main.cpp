// 情境：线程的结果放在共享变量里。两个线程各算一半，把结果写进外面的两个变量，
// main 必须记得 join 之后才能读——读早了就是数据竞争；结果和线程的关系也只靠约定。
// 组织手段：把「并发任务」与「它的结果」绑在一起——std::async 启动任务，返回 std::future，
// get() 会等任务完成再取出结果，不需要共享可写变量。
// 依据：C++ Core Guidelines CP.4「按任务而不是线程思考」、CP.60「用 future 从并发任务返回值」、
// CP.61「用 async() 启动并发任务」、CP.3「尽量少显式共享可写数据」。
//
// 实验：
// 1. 保留 sumRange()。用 std::async(std::launch::async, sumRange, 1, 50) 与
//    std::async(std::launch::async, sumRange, 51, 100) 启动两个任务，得到两个 std::future<long>。
// 2. 用两个 get() 的和输出 async total=5050。删掉线程和共享变量，解开 TODO(实验) 段。
#include <future>
#include <iostream>
#include <thread>

long sumRange(int from, int to) {
    long s = 0;
    for (int i = from; i <= to; ++i) s += i;
    return s;
}

int main() {
    long left = 0, right = 0;            // 共享的可写变量
    std::thread t1([&] { left = sumRange(1, 50); });
    std::thread t2([&] { right = sumRange(51, 100); });
    t1.join();                           // 忘了 join 就去读，就是数据竞争
    t2.join();
    std::cout << "thread total=" << left + right << "\n";

    // TODO(实验)：改用 std::async 与 std::future 后，删掉上面六行，解开下面这段
    // auto f1 = std::async(std::launch::async, sumRange, 1, 50);
    // auto f2 = std::async(std::launch::async, sumRange, 51, 100);
    // std::cout << "async total=" << f1.get() + f2.get() << "\n";
}
