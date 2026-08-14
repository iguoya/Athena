#include "raii.hpp"

#include <ostream>

using namespace std;

void RAII::unique(ostream& output) {
    // TODO: 演示 unique_ptr 的独占所有权、创建和所有权转移。
    output << "[待实现] 独占指针" << '\n';
}

void RAII::shared(ostream& output) {
    // TODO: 演示 shared_ptr 的共享所有权和引用计数。
    output << "[待实现] 共享指针" << '\n';
}

void RAII::weak(ostream& output) {
    // TODO: 演示 weak_ptr 的观察语义以及如何避免循环引用。
    output << "[待实现] 弱引用指针" << '\n';
}
