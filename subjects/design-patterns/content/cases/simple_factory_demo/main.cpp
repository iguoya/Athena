// 简单工厂：一个工厂按参数造产品。
// 实验：运行后新增 ProductC——你必须同时改 SimpleFactory::create 的分支，
// 这个「不得不改旧代码」的位置就是它违反开闭原则的地方（工厂方法会治好它）。
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

class SimpleFactory {
public:
    static std::unique_ptr<Product> create(const std::string& type) {
        if (type == "A") return std::make_unique<ProductA>();
        if (type == "B") return std::make_unique<ProductB>();
        return nullptr;   // 每加一种产品这里就要改一行——违反 OCP 的位置
    }
};

int main() {
    for (const std::string& t : {"A", "B"}) {
        auto p = SimpleFactory::create(t);
        if (p) p->use();
    }
}
