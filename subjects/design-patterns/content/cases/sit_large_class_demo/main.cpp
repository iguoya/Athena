// 情境：过大的类。Order 里既有订单自己的事（金额），又揣着收货地址的四个字段，
// 地址的格式化和邮编校验也都写在 Order 里。现在发货单 Shipment 也要用同样的地址——
// 只能把这些字段和逻辑再抄一份。
// 重构手法：提炼类（Extract Class），《重构》第 2 版第 3 章「过大的类」：字段带着相同前缀或后缀的
// 那一组，往往就是一个该独立出来的类；看使用者只用到类的哪一部分，也是切分的线索。
//
// 实验：
// 1. 提炼出 class Address：持有 street、city、zip；有 bool validZip() const（邮编正好 6 位）
//    和 std::string oneLine() const（格式 "<street>, <city> <zip>"）。
// 2. Order 改为持有一个 Address，label() 和邮编校验改为委托给它，输出保持不变。
// 3. 新需求：写 struct Shipment { Address to; int kg; }，用 Address 打印发货行：
//    "ship: <oneLine> valid=yes|no"。解开 main 里的 TODO(实验) 行。
#include <iostream>
#include <string>

class Order {
public:
    Order(std::string customer, std::string street, std::string city, std::string zip, int total)
        : customer_(std::move(customer)), street_(std::move(street)), city_(std::move(city)),
          zip_(std::move(zip)), total_(total) {}

    int total() const { return total_; }
    std::string label() const { return customer_ + ", " + street_ + ", " + city_ + " " + zip_; }
    bool validZip() const { return zip_.size() == 6; }

private:
    std::string customer_;
    std::string street_;
    std::string city_;
    std::string zip_;
    int total_;
};

int main() {
    Order order("王芳", "中山路 1 号", "杭州", "310000", 1200);
    std::cout << "order: " << order.label() << " valid=" << (order.validZip() ? "yes" : "no") << "\n";
    // TODO(实验)：提炼 Address、写好 Shipment 后，解开下面两行
    // Shipment shipment{Address("中山路 1 号", "杭州", "310000"), 3};
    // std::cout << "ship: " << shipment.to.oneLine() << " valid=" << (shipment.to.validZip() ? "yes" : "no") << "\n";
}
