// 情境：手写 lock()/unlock()。deposit() 在金额非法时抛异常，跳过了后面的 unlock()——
// 互斥量一直锁着，之后所有线程都会卡在这把锁上。
// 组织手段：锁也是资源，交给 RAII——std::lock_guard / std::scoped_lock 构造时加锁、
// 析构时解锁；并且把互斥量和它保护的数据放在同一个类里。
// 依据：C++ Core Guidelines CP.20「用 RAII，绝不直接调用 lock()/unlock()」、
// CP.44「记得给 lock_guard 和 unique_lock 起名字」、CP.50「把互斥量和它保护的数据定义在一起」。
//
// 实验：
// 1. 把 deposit() 里的 m_.lock() / m_.unlock() 换成 std::lock_guard<std::mutex> guard(m_);
//    （一定要有变量名 guard——不起名的临时对象会在本行结束就析构，等于没加锁）。
// 2. balance() 同样用 lock_guard。
// 3. 运行后应输出 mutex free 与 balance=100。
#include <iostream>
#include <mutex>
#include <stdexcept>
#include <thread>

class Account {
public:
    void deposit(int amount) {
        m_.lock();
        // TODO(实验)：换成 lock_guard，删掉手写的 lock/unlock
        if (amount <= 0) throw std::invalid_argument("amount must be positive");
        balance_ += amount;
        m_.unlock();
    }
    int balance() {
        m_.lock();
        int b = balance_;
        m_.unlock();
        return b;
    }
    bool mutexFree() {                   // 演示用：另一个线程能立刻拿到锁，说明没人占着
        bool free = false;               // （持有锁的线程自己 try_lock 是未定义行为，所以换个线程试）
        std::thread probe([&] {
            if (m_.try_lock()) { free = true; m_.unlock(); }
        });
        probe.join();
        return free;
    }
    void releaseLeakedLock() { m_.unlock(); }   // 演示用：由仍持有锁的本线程解开，免得销毁锁着的互斥量
private:
    std::mutex m_;                       // 和它保护的 balance_ 放在一起（CP.50）
    int balance_ = 0;
};

int main() {
    Account acc;
    acc.deposit(100);
    try {
        acc.deposit(-5);
    } catch (const std::invalid_argument& e) {
        std::cout << "rejected: " << e.what() << "\n";
    }
    if (acc.mutexFree()) {
        std::cout << "mutex free\n";
        std::cout << "balance=" << acc.balance() << "\n";
    } else {
        std::cout << "mutex still locked after exception\n";
        acc.releaseLeakedLock();
    }
}
