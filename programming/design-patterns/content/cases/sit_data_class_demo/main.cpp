// 情境：纯数据类。Account 只有公开字段，处理它的逻辑散在外面的自由函数和 main 里：
// 谁都可以直接 acc.balance -= n，「余额不足不许取」的规则要靠每个调用方自己记得检查。
// 重构手法：封装记录（Encapsulate Record）、移除设值函数（Remove Setting Method）、
// 搬移函数（Move Function），《重构》第 2 版第 3 章「纯数据类」：数据类往往说明行为放错了
// 地方，把行为从调用方搬进数据类，进展会很大。
//
// 实验：
// 1. 把 balance 改成私有，提供 int balance() const；deposit() 与 statement() 搬成成员函数。
// 2. 新增 bool withdraw(int amount)：余额不足时返回 false 且余额不变，否则扣款返回 true。
//    取款的规则只在这一处。
// 3. 解开 main 里的 TODO(实验) 行：取 5000 应被拒绝，余额仍是 700。
#include <iostream>
#include <string>

struct Account {
    std::string owner;
    int balance;
};

void deposit(Account& a, int amount) { a.balance += amount; }
std::string statement(const Account& a) { return a.owner + ": " + std::to_string(a.balance); }

int main() {
    Account acc{"王芳", 1000};
    deposit(acc, 200);
    acc.balance -= 500;   // 调用方自己扣款，没人替它检查余额
    std::cout << statement(acc) << "\n";
    std::cout << "balance=" << acc.balance << "\n";
    // TODO(实验)：改成私有字段、写好成员函数后，把上面的 acc.balance 两处改掉，并解开下面几行
    // bool ok = acc.withdraw(5000);
    // std::cout << "withdraw 5000: " << (ok ? "ok" : "refused") << "\n";
    // std::cout << "balance=" << acc.balance() << "\n";
}
