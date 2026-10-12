// 策略：定义一系列算法，把它们一个个封装起来，并且使它们可以相互替换。
// 改编自软设教程（第 5 版）例 7.8「购物中心收银软件」：正常收费、打折、满额返利三种策略。
// 实验：先预测——消费 700 元，满 300 返 100 应收多少？
// 补 TODO：实现 CashReturn::acceptCash()——每满 moneyCondition 就减 moneyReturn。
// CashContext 与另外两种策略一行不改。
#include <cmath>
#include <iostream>
#include <memory>

// Strategy：所有收费算法的公共接口
class CashSuper {
public:
    virtual ~CashSuper() = default;
    virtual double acceptCash(double money) const = 0;
};

// ConcreteStrategy：正常收费
class CashNormal : public CashSuper {
public:
    double acceptCash(double money) const override { return money; }
};

// ConcreteStrategy：打折
class CashDiscount : public CashSuper {
public:
    explicit CashDiscount(double rate) : rate_(rate) {}
    double acceptCash(double money) const override { return money * rate_; }
private:
    double rate_;
};

// ConcreteStrategy：满额返利
class CashReturn : public CashSuper {
public:
    CashReturn(double condition, double ret) : moneyCondition(condition), moneyReturn(ret) {}
    double acceptCash(double money) const override {
        // TODO(实验)：money 每满 moneyCondition 减去 moneyReturn（提示：std::floor(money / moneyCondition)）
        return money;
    }
private:
    double moneyCondition;
    double moneyReturn;
};

// Context：用一个 Strategy 来配置，调用时只认接口
class CashContext {
public:
    explicit CashContext(std::unique_ptr<CashSuper> s) : cs_(std::move(s)) {}
    double getResult(double money) const { return cs_->acceptCash(money); }
private:
    std::unique_ptr<CashSuper> cs_;
};

int main() {
    CashContext normal(std::make_unique<CashNormal>());
    CashContext discount(std::make_unique<CashDiscount>(0.8));
    CashContext ret(std::make_unique<CashReturn>(300, 100));
    std::cout << "normal: " << normal.getResult(700) << "\n";
    std::cout << "discount: " << discount.getResult(700) << "\n";
    std::cout << "return: " << ret.getResult(700) << "\n";
}
