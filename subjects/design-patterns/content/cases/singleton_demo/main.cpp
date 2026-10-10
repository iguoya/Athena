// 单例模式：Meyers 单例（C++11 起局部静态变量的初始化是线程安全的）
// 实验：先预测「Singleton constructed」会打印几次，再运行核对；
// 然后补 TODO：比较两处拿到的引用地址，相同就输出一行 same instance: yes。
// 最后解开 main 末尾的注释行，看编译器怎么拦住外部构造。
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

// 模拟另一个模块：它也只能从 getInstance() 拿实例
void otherModule() { Singleton::getInstance().business(); }

int main() {
    Singleton& a = Singleton::getInstance();
    a.business();
    otherModule();
    Singleton& b = Singleton::getInstance();

    // TODO(实验)：比较 &a 与 &b，相同则输出一行 same instance: yes
    (void)b;

    // Singleton s;                       // 解开注释：编译错误，构造私有
    // Singleton* p = new Singleton();    // 同样被拦
    return 0;
}
