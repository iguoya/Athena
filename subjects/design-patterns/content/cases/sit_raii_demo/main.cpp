// 情境：资源泄漏。openRes/closeRes 是一对 C 风格接口（真实程序里是文件、锁、套接字）。
// process() 在中途出错时提前 return，忘了 closeRes——资源就漏了。每多一个 return、
// 每多一处可能抛异常的调用，就多一个漏关的机会。
// 组织手段：RAII——资源的获取放在构造函数，释放放在析构函数，离开作用域自动释放。
// 规范：C++ Core Guidelines R.1「用资源句柄与 RAII 自动管理资源」、E.6「用 RAII 防止泄漏」。
//
// 实验：
// 1. 写 class Resource：构造函数调 openRes(name) 并保存句柄，析构函数调 closeRes。
//    禁止拷贝（Resource(const Resource&) = delete; 赋值同理），免得两个对象关同一个句柄。
// 2. 把 process() 改成用 Resource，删掉所有手写的 closeRes——无论从哪个 return 离开都会关闭。
// 3. 运行后最后一行应是 leaked=0。
#include <iostream>
#include <string>

// —— 模拟的 C 风格资源接口（不要改）——
struct Handle { std::string name; };
int g_open = 0;
Handle* openRes(const std::string& name) {
    ++g_open;
    std::cout << "open " << name << "\n";
    return new Handle{name};
}
void closeRes(Handle* h) {
    --g_open;
    std::cout << "close " << h->name << "\n";
    delete h;
}

// —— 业务代码 ——
// TODO(实验)：在这里写 class Resource，并让 process() 用它管理句柄
bool process(const std::string& name, bool fail) {
    Handle* h = openRes(name);
    if (fail) {
        std::cout << "error while processing " << name << "\n";
        return false;   // 这里忘了 closeRes(h)
    }
    std::cout << "processed " << name << "\n";
    closeRes(h);
    return true;
}

int main() {
    process("a.txt", false);
    process("b.txt", true);
    std::cout << "leaked=" << g_open << "\n";
}
