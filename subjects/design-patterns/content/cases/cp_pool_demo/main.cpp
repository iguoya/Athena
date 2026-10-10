// 情境：每个任务起一个线程。100 个小任务就创建 100 个线程——线程的创建和销毁很贵，
// 任务一多还会把系统线程数用光。
// 组织手段：预先建好固定数量的工作线程，任务放进队列，工作线程循环取任务执行（生产者–消费者）；
// 收工时「关闭」队列，工作线程把剩下的任务做完再退出。
// 依据：C++ Core Guidelines CP.41「尽量少创建和销毁线程」（原文示例就是“每条消息一个线程”与
// “一组预先创建好的工作线程”的对比）、CP.42「不要不带条件地 wait」。
//
// 实验：
// 1. 补完 TaskQueue：close() 置 closed_ 并 notify_all；
//    pop(out)：用 unique_lock 与带谓词的 wait（队列非空或已关闭），
//    队列为空且已关闭时返回 false，否则取出队首赋给 out 并返回 true——
//    所以关闭前放进去的任务一个都不会丢。
// 2. 解开 main 里的 TODO(实验) 块：4 个工作线程消费 100 个任务，并把「每任务一线程」的旧循环删掉。
//    达标时输出 workers=4 tasks=100 total=5050，结果是确定的，与线程调度无关。
#include <condition_variable>
#include <functional>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>

class TaskQueue {
public:
    void push(std::function<void()> t) {
        {
            std::lock_guard<std::mutex> lock(m_);
            q_.push(std::move(t));
        }
        cv_.notify_one();
    }
    void close() {
        // TODO(实验)：加锁置 closed_，然后 cv_.notify_all()
    }
    bool pop(std::function<void()>& out) {
        // TODO(实验)：unique_lock + cv_.wait(lock, [this] { return !q_.empty() || closed_; })；
        //             队列空（此时必然已关闭）返回 false，否则取队首给 out，返回 true
        (void)out;
        return false;
    }

private:
    std::mutex m_;
    std::condition_variable cv_;
    std::queue<std::function<void()>> q_;
    bool closed_ = false;
};

std::mutex totalMutex;
long total = 0;
void work(int n) {
    std::lock_guard<std::mutex> lock(totalMutex);
    total += n;
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 1; i <= 100; ++i) threads.emplace_back(work, i);   // 每个任务一个线程
    for (auto& t : threads) t.join();
    std::cout << "threads=" << threads.size() << " total=" << total << "\n";
    // TODO(实验)：补完 TaskQueue 后，删掉上面的 threads 部分（连同 total 的输出），换成下面几行
    // TaskQueue q;
    // std::vector<std::thread> workers;
    // for (int w = 0; w < 4; ++w)
    //     workers.emplace_back([&q] { std::function<void()> t; while (q.pop(t)) t(); });
    // for (int i = 1; i <= 100; ++i) q.push([i] { work(i); });
    // q.close();
    // for (auto& w : workers) w.join();
    // std::cout << "workers=" << workers.size() << " tasks=100 total=" << total << "\n";
}
