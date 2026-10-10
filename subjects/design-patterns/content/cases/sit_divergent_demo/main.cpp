// 情境：发散式变化。Employee 一个类里同时装着「算工资」与「出报表」：工资规则变了要改它，
// 报表格式变了也要改它——一个类因为两种不相干的原因而变化。
// 重构手法：提炼类（Extract Class）、搬移函数（Move Function），《重构》第 2 版；对应单一职责原则。
//
// 实验：
// 1. 把 pay() 的计算搬到 class PayCalculator（成员函数 int pay(const Employee&) const）。
// 2. 把文本报表搬到 class TextReport（成员函数 std::string render(const Employee&, int pay) const）。
//    Employee 只保留数据。
// 3. 新需求：加 class JsonReport，render 输出 {"name":"zhang","pay":12500}。
//    工资计算一行不改。解开 main 里的 TODO(实验) 段。
#include <iostream>
#include <string>

class Employee {
public:
    std::string name;
    int baseSalary;
    int overtimeHours;

    // 工资规则：每小时加班费 150
    int pay() const { return baseSalary + overtimeHours * 150; }

    // 报表格式
    std::string report() const {
        return "员工 " + name + " 本月应发 " + std::to_string(pay()) + " 元";
    }
};

int main() {
    Employee e{"zhang", 11000, 10};
    std::cout << e.report() << "\n";

    // TODO(实验)：拆出 PayCalculator、TextReport、JsonReport 后，删掉上面一行，解开下面这段
    // PayCalculator calc;
    // int p = calc.pay(e);
    // std::cout << TextReport{}.render(e, p) << "\n";
    // std::cout << JsonReport{}.render(e, p) << "\n";
}
