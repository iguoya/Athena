// 情境：重复代码。零售价和批发价各抄了一份「运费规则」，两处只差折扣那一行。
// 现在运营要求把运费规则改成「满 199 免运费」——抄了两份，就得改两处，漏一处价格就对不上。
// 重构手法：提炼函数（Extract Function），《重构》第 2 版第 3 章「重复代码」。
//
// 实验：
// 1. 提炼出 int shipping(int net, int kg)：净额达到免运费线则基础运费为 0，否则 10 元；
//    重量超过 5 公斤的部分，每公斤另加 2 元（任何情况都加）。
// 2. retailTotal() 与 wholesaleTotal() 都改为调用 shipping()。
// 3. 免运费线从 99 改成 199——只允许改 shipping() 里这一处。
// 4. 新需求：增加 groupBuyTotal(amount, kg)：先打七折（amount * 7 / 10），再加运费。
//    解开 main 里的 TODO(实验) 行。达标时会输出 retail=166 wholesale=240 group=702。
#include <iostream>

// 零售：不打折，运费按原价算。
int retailTotal(int amount, int kg) {
    int ship = amount >= 99 ? 0 : 10;
    if (kg > 5) ship += (kg - 5) * 2;
    return amount + ship;
}

// 批发：先打八折，运费按折后价算。
int wholesaleTotal(int amount, int kg) {
    int net = amount * 8 / 10;
    int ship = net >= 99 ? 0 : 10;
    if (kg > 5) ship += (kg - 5) * 2;
    return net + ship;
}

int main() {
    std::cout << "retail=" << retailTotal(150, 8)
              << " wholesale=" << wholesaleTotal(300, 2) << "\n";
    // TODO(实验)：提炼 shipping()、改好免运费线并写好 groupBuyTotal() 后，把上面两行换成下一行
    // std::cout << "retail=" << retailTotal(150, 8) << " wholesale=" << wholesaleTotal(300, 2) << " group=" << groupBuyTotal(1000, 6) << "\n";
}
