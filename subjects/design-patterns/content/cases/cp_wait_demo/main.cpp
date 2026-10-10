// 情境：不带条件地取数据。消费者线程直接从队列里取，队列还空着就拿到一个默认值 0；
// 用 sleep 去「等一会儿」只是碰运气。
// 组织手段：条件变量 + 谓词——消费者在锁内 wait 一个条件（队列非空），生产者放入数据后
// notify；带谓词的 wait 也能正确处理虚假唤醒。
// 依据：C++ Core Guidelines CP.42「不要不带条件地 wait」。
//
// 实验：
// 1. BlockingQueue 增加一个 std::condition_variable cv_。
// 2. push()：加锁放入数据后 cv_.notify_one()。
// 3. pop()：用 std::unique_lock 加锁，cv_.wait(lock, [this] { return !q_.empty(); })，
//    然后取出队首。删掉「队列为空时返回 0」的分支。
// 4. 运行后应输出 sum=15（消费者拿到了生产者放入的 1 到 5）。
#include <chrono>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>

class BlockingQueue {
public:
    void push(int v) {
        std::lock_guard<std::mutex> lock(m_);
        q_.push(v);
        // TODO(实验)：通知一个等待者
    }
    int pop() {
        std::lock_guard<std::mutex> lock(m_);
        // TODO(实验)：改成 unique_lock + 带条件的 wait，删掉下面这个分支
        if (q_.empty()) return 0;          // 没有数据就返回 0——调用方分不出真假
        int v = q_.front();
        q_.pop();
        return v;
    }
private:
    std::mutex m_;
    std::queue<int> q_;
};

int main() {
    BlockingQueue q;
    int sum = 0;
    std::thread consumer([&] {
        for (int i = 0; i < 5; ++i) sum += q.pop();
    });
    std::thread producer([&] {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));   // 生产者晚一点才开始
        for (int i = 1; i <= 5; ++i) q.push(i);
    });
    producer.join();
    consumer.join();
    std::cout << "sum=" << sum << "\n";
}
