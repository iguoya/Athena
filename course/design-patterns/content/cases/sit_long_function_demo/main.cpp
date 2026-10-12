// 情境：过长函数。printReport() 一口气做了三件事：汇总金额、按规则算折扣、排版输出。
// 现在要求再导出一种 CSV 格式——汇总和折扣逻辑都锁在这个长函数里，只能复制一遍。
// 重构手法：提炼函数（Extract Function）、拆分阶段（Split Phase），《重构》第 2 版。
// 规范：C++ Core Guidelines F.2「一个函数只做一件逻辑上的事」、F.3「函数短小简单」。
//
// 实验：
// 1. 从 printReport() 里提炼出 Summary summarize(const std::vector<Order>&)：只负责算出
//    总额 total、折扣 discount、应付 payable（满 1000 打九折，折扣取整到分）。
// 2. printReport() 改成调用 summarize() 再排版。
// 3. 新需求：写 std::string toCsv(const Summary&)，输出两行：表头 total,discount,payable
//    与数值行。解开 main 里的 TODO(实验) 行。达标时会输出 1200,120,1080。
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

struct Order {
    std::string item;
    int quantity;
    int unitPrice;   // 单位：元
};

struct Summary {
    int total = 0;
    int discount = 0;
    int payable = 0;
};

void printReport(const std::vector<Order>& orders) {
    int total = 0;
    for (const auto& o : orders) total += o.quantity * o.unitPrice;
    int discount = 0;
    if (total >= 1000) discount = total / 10;
    int payable = total - discount;
    std::cout << "==== 结算单 ====\n";
    for (const auto& o : orders) std::cout << o.item << " x" << o.quantity << " = " << o.quantity * o.unitPrice << "\n";
    std::cout << "合计 " << total << "，优惠 " << discount << "，应付 " << payable << "\n";
}

int main() {
    std::vector<Order> orders{{"键盘", 2, 300}, {"显示器", 1, 600}};
    printReport(orders);
    // TODO(实验)：提炼出 summarize() 并写好 toCsv() 后，解开下一行
    // std::cout << toCsv(summarize(orders));
}
