// 转发函数里用 std::move 会掏空调用方的左值
//
// Core Guidelines F.19：转发参数写成 TP&&，并且只用 std::forward 转发它。
// 这个案例把「用错成 std::move」的后果摆出来——它的现场在调用方那边。

#include <iostream>
#include <string>
#include <utility>

using namespace std;

struct Sink {
    string taken;
    void accept(const string& s) { taken = s;  cout << "    下一层：拷贝了「" << s << "」\n"; }
    void accept(string&& s)      { taken = std::move(s); cout << "    下一层：搬走了「" << taken << "」\n"; }
};

// —— 示范：正确的转发 ——
// TP&& 既忽略又保留实参的 const 与右值性：这个函数自己不关心，
// 但要原样传给真正关心的下一层（F.19 的原话）。
template <typename T>
void forward_it(Sink& sink, T&& value) {
    sink.accept(std::forward<T>(value));
}

// —— 示范：错误的转发 ——
// std::move 无条件转成右值，不看实参原本是什么。
template <typename T>
void move_it(Sink& sink, T&& value) {
    sink.accept(std::move(value));
}

void demo_forward() {
    Sink sink;
    string owned = "调用方的字符串";

    cout << "[std::forward] 传左值\n";
    forward_it(sink, owned);
    cout << "    调用方手里还剩：「" << owned << "」\n";
}

void demo_move() {
    Sink sink;
    string owned = "调用方的字符串";

    cout << "[std::move] 传同一个左值\n";
    move_it(sink, owned);
    cout << "    调用方手里还剩：「" << owned << "」\n";
}

// —— 待填 ——
// TODO(学员)：在下面写一行，用 forward_it 传一个**右值**给 sink：
//     forward_it(sink, std::string{"临时的字符串"});
//
// 先预测：
//   1. 这次下一层是「拷贝」还是「搬走」？
//   2. 同一个 forward_it，为什么传左值时是拷贝、传右值时是搬走？
//      T 在这两种情况下分别被推导成什么？
void todo_forward_rvalue() {
    Sink sink;
    cout << "[std::forward] 传右值\n";

    cout << "    （还没写）\n";
}

// —— 以下驱动请勿改 ——
int main() {
    demo_forward();
    cout << "---\n";
    demo_move();
    cout << "---\n";
    todo_forward_rvalue();
    return 0;
}
