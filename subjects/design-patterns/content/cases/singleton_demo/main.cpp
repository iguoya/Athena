// 单例模式：Meyers 单例（C++11 起线程安全）
// 实验：运行两次 getInstance()，确认地址相同；再解开 main 里的注释行，
// 体验编译器如何阻止外部 new Singleton。
#include <iostream>

class Singleton {
public:
    static Singleton& getInstance() {
        static Singleton instance;   // 首次调用才构造（Meyers 单例）
        return instance;
    }
    void business() { std::cout << "Singleton@" << this << " working\n"; }
private:
    Singleton() { std::cout << "Singleton constructed\n"; }
    ~Singleton() = default;
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
};

int main() {
    Singleton::getInstance().business();
    Singleton::getInstance().business();
    // Singleton s;             // 解开注释：编译错误，构造私有
    // Singleton* p = new Singleton();  // 同样被拦
    return 0;
}
