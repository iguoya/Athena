// 情境：到处都在判断「是不是空」。findCustomer() 查不到就返回 nullptr，于是每个用到客户的
// 地方都要写一遍 if (c)——名字怎么显示、折扣多少，各有各的空判断，漏一处就是空指针。
// 重构手法：引入特例（Introduce Special Case，早期版本叫引入 Null 对象），《重构》第 2 版
// 第 10 章。Null Object 模式见 Bobby Woolf 的《The Null Object Pattern》（PLoPD3，1998）。
//
// 实验：
// 1. 让 findCustomer() 查不到时返回一个「访客」特例对象的引用（名字"访客"，折扣 0），
//    返回类型改为 const Customer&。
// 2. 删掉 label()、discountOf()、payable() 里全部的空判断，直接用引用。
// 3. 新需求：写 std::string receiptLine(const Customer&, int amount)，格式
//    "<名字> pays <实付>"。调用它的地方不允许有任何 if。解开 main 里的 TODO(实验) 行。
#include <iostream>
#include <string>

struct Customer {
    std::string name;
    int discountPercent;
};

const Customer* findCustomer(int id) {
    static const Customer wang{"王芳", 10};
    if (id == 7) return &wang;
    return nullptr;
}

std::string label(const Customer* c) { return c ? c->name : "访客"; }
int discountOf(const Customer* c) { return c ? c->discountPercent : 0; }
int payable(int amount, const Customer* c) { return amount - amount * discountOf(c) / 100; }

int main() {
    for (int id : {7, 99}) {
        const Customer* c = findCustomer(id);
        std::cout << label(c) << " -> " << payable(100, c) << "\n";
    }
    // TODO(实验)：改成特例对象、写好 receiptLine() 后，把上面的循环换成下面几行
    // for (int id : {7, 99}) {
    //     std::cout << "receipt: " << receiptLine(findCustomer(id), 100) << "\n";
    // }
}
