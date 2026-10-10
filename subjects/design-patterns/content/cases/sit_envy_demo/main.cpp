// 情境：依恋情结与过长的消息链。shippingFee() 写在结算模块里，却一路穿过
// order → customer → address 去读城市；只要 Customer 或 Address 的结构一变，结算模块就要跟着改。
// 重构手法：隐藏委托关系（Hide Delegate）、搬移函数（Move Function），《重构》第 2 版；对应迪米特法则。
//
// 实验：
// 1. 给 Order 加一个成员函数 std::string shippingCity() const，由它去问 customer 的地址——
//    外部不再需要知道 Order 里面有 Customer、Customer 里面有 Address。
// 2. 把运费计算搬进 Order：int shippingFee() const（上海 10 元，其他城市 18 元）。
// 3. 解开 main 里的 TODO(实验) 段。达标时会输出 order 2 fee=18。
#include <iostream>
#include <string>

struct Address {
    std::string city;
};

struct Customer {
    std::string name;
    Address address;
    const Address& getAddress() const { return address; }
};

struct Order {
    int id;
    Customer customer;
    const Customer& getCustomer() const { return customer; }
};

// 结算模块：依恋着 Order、Customer、Address 三个类的内部结构
int shippingFee(const Order& o) {
    if (o.getCustomer().getAddress().city == "上海") return 10;
    return 18;
}

int main() {
    Order a{1, {"li", {"上海"}}};
    std::cout << "order " << a.id << " fee=" << shippingFee(a) << "\n";

    // TODO(实验)：给 Order 加好 shippingCity() 与 shippingFee() 后，解开下面三行
    // Order b{2, {"wang", {"成都"}}};
    // std::cout << "order " << b.id << " city=" << b.shippingCity() << "\n";
    // std::cout << "order " << b.id << " fee=" << b.shippingFee() << "\n";
}
