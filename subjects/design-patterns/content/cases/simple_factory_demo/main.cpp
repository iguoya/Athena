// 简单工厂：一个工厂按参数造产品。
// 实验：main 已经在要 "C" 了，可工厂还不认识它。补 TODO：新增 ProductC
// （use() 输出 use ProductC），并让工厂认出 "C"。
// 你不得不改 SimpleFactory::create 的分支——这个「不得不改旧代码」的位置
// 就是它违反开闭原则的地方（工厂方法会治好它）。
#include <iostream>
#include <memory>
#include <string>

class Product {
public:
    virtual ~Product() = default;
    virtual void use() = 0;
};
class ProductA : public Product {
public: void use() override { std::cout << "use ProductA\n"; }
};
class ProductB : public Product {
public: void use() override { std::cout << "use ProductB\n"; }
};
// TODO(实验)：在这里新增 ProductC

class SimpleFactory {
public:
    static std::unique_ptr<Product> create(const std::string& type) {
        if (type == "A") return std::make_unique<ProductA>();
        if (type == "B") return std::make_unique<ProductB>();
        // TODO(实验)：认出 "C"——每加一种产品这里就要改一行，违反 OCP 的位置
        return nullptr;
    }
};

int main() {
    for (const char* t : {"A", "B", "C"}) {
        auto p = SimpleFactory::create(t);
        if (p) p->use();
        else std::cout << "unknown product: " << t << "\n";
    }
}
