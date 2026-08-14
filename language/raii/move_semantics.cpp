#include "raii.hpp"

#include <ostream>

using namespace std;

void RAII::rvalue(ostream& output) {
    // TODO: 演示左值、右值和右值引用的基本区别。
    output << "[待实现] 右值引用" << '\n';
}

void RAII::move_(ostream& output) {
    // TODO: 演示移动构造、移动赋值和 std::move。
    output << "[待实现] 移动构造与赋值" << '\n';
}
