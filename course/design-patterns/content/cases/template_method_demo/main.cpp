// 模板方法：父类定义算法骨架，把其中某些步骤延迟到子类实现。
// 实验：Beverage::prepare() 是模板方法，固定了「烧水 → 冲泡 → 倒杯 → 加料」的顺序。
// Coffee 已经写好。补 TODO：写 Tea（brew 输出 steeping tea，addCondiments 输出 adding lemon），
// 并在 main 里调用它的 prepare()。prepare() 本身一行不改，子类也改不了它的顺序。
#include <iostream>

// AbstractClass：模板方法 + 原语操作
class Beverage {
public:
    virtual ~Beverage() = default;
    // 模板方法：不是虚函数，子类不能改变步骤顺序
    void prepare() {
        boilWater();
        brew();
        pourInCup();
        if (wantsCondiments()) addCondiments();
    }
protected:
    virtual void brew() = 0;           // 原语操作：子类必须实现
    virtual void addCondiments() = 0;  // 原语操作：子类必须实现
    virtual bool wantsCondiments() { return true; }  // 钩子：有默认行为，子类可选择重定义
private:
    void boilWater() { std::cout << "boiling water\n"; }
    void pourInCup() { std::cout << "pouring into cup\n"; }
};

// ConcreteClass
class Coffee : public Beverage {
protected:
    void brew() override { std::cout << "dripping coffee\n"; }
    void addCondiments() override { std::cout << "adding milk\n"; }
};

// TODO(实验)：在这里新增 Tea

int main() {
    Coffee coffee;
    coffee.prepare();
    std::cout << "--\n";
    // TODO(实验)：Tea tea; tea.prepare();
}
